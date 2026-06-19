import traceback
import functools
import argparse
import pwnshop
import pwnlib.context
import pwnlib.log
import signal
import random
import shutil
import ezmp
import yaml
import glob
import sys
import os

pwnlib.log.install_default_handler()

def challenge_class(challenge):
    if ":" not in challenge:
        assert challenge in pwnshop.ALL_CHALLENGES, "Unknown challenge specified!"
        return pwnshop.ALL_CHALLENGES[challenge]
    else:
        module, level_src = challenge.split(":")
        level = int(level_src)

        assert module in pwnshop.MODULE_LEVELS, "Uknown module specified!"
        assert 0 < level <= len(pwnshop.MODULE_LEVELS[module]), "Invalid level specified."
        return pwnshop.MODULE_LEVELS[module][level-1]

def with_challenges(f):
    @functools.wraps(f)
    def f_with_challenge(args):
        challenges = [ ]
        kwargs = {
            "seed": args.seed,
            "walkthrough": args.walkthrough,
            "style": not args.no_style,
            "work_dir": args.workdir,
        }

        if args.debug_output:
            pwnlib.context.context.log_level = "DEBUG"

        if args.image:
            kwargs["environment"] = pwnshop.DockerEnvironment(args.image)

        for m in (args.module or [ ]) if "module" in args else [ ]:
            challenges += [
                c(**kwargs)
                for c in pwnshop.MODULE_LEVELS[m]
            ]

        if args.challenges:
            challenges += [
                challenge_class(challenge=c)(**kwargs)
                for c in args.challenges
            ]

        if not challenges:
            challenges += [
                c(**kwargs)
                for c in pwnshop.ALL_CHALLENGES.values()
            ]

        if getattr(args, "debug_symbols", None):
            for c in challenges:
                c.DEBUG_SYMBOLS = args.debug_symbols

        return f(args, challenges)
    return f_with_challenge

@with_challenges
def handle_render(args, challenges):
    for challenge in challenges:
        if isinstance(challenge, pwnshop.ChallengeGroup):
            for name,src in challenge.render().items():
                for i, line in enumerate(src.splitlines()):
                    print(f"{name}:{i + 1}\t{line}")
                print()
        else:
            src = challenge.render()
            if not args.line_numbers:
                print(src)
            else:
                for i, line in enumerate(src.splitlines()):
                    print(f"{i + 1}\t{line}")

def handle_list(args): #pylint:disable=unused-argument
    for module,challenges in pwnshop.MODULE_LEVELS.items():
        for n,challenge in enumerate(challenges, start=1):
            print(f"{module}:{n} --- {challenge.__name__}")

@with_challenges
def handle_build(args, challenges):
    for challenge in challenges:
        with challenge:
            if args.debug_output:
                challenge._owns_workdir = False

            challenge.build()

def raise_timeout(signum, stack):
    raise TimeoutError("ACTION TIMED OUT")

def verify_challenge(challenge, debug=False, flag=None, strace=False):
    if debug:
        pwnlib.context.context.log_level = "DEBUG"

    if flag:
        with open("/flag", "wb") as f:
            f.write(flag.encode())

    challenge.render()
    challenge.build()

    os.chdir(challenge.work_dir)
    return challenge.verify(strace=strace)

@with_challenges
def handle_verify(args, challenges):
    failures = [ ]
    for challenge in challenges:
        name = challenge.__name__ if type(challenge) is type else type(challenge).__name__

        print(f"VERIFYING: {name}")

        try:
            if type(challenge) is type:
                challenge = challenge(seed=args.seed, walkthrough=args.walkthrough, style=not args.no_style, work_dir=args.workdir)

            if args.timeout:
                signal.signal(signal.SIGALRM, raise_timeout)
                signal.alarm(args.timeout)

            with challenge:
                if args.debug_output:
                    challenge._owns_workdir = False
                verify_challenge(challenge, debug=args.debug_output, flag=args.flag, strace=args.strace)
            signal.alarm(0)
            print(f"SUCCEEDED: {name}")
        except NotImplementedError:
            failures.append(challenge)
            print(f"MISSING: {name}")
        except Exception: #pylint:disable=broad-exception-caught
            print(traceback.format_exc())
            failures.append(challenge)
            print(f"FAILED: {name}")

    return not failures

def get_first(where, what, *default):
    try:
        return next(ds[what] for ds in where if what in ds)
    except StopIteration:
        if default:
            return default[0]
        else:
            raise KeyError(what) #pylint:disable=raise-missing-from

def handle_apply(args):
    if args.debug_output:
        pwnlib.context.context.log_level = "DEBUG"

    yaml_dir = os.path.abspath(os.path.dirname(args.yaml))
    y = yaml.safe_load(open(args.yaml))
    name_prefix = y.get("binary_name_prefix", None)

    background_runner = ezmp.Task(noop=not args.mp, buffer_output=True, silence_successes=args.quiet)

    for c in y['challenges']:
        cid = c["id"]

        data_sources = [
            c, c.get("auxiliary", {}).get("pwnshop", {}),
            y, y.get("auxiliary", {}).get("pwnshop", {}),
            vars(args),
        ]

        try:
            class_name = get_first(data_sources, "challenge")
        except KeyError:
            print(f"No pwnshop class for challenge {cid}. Skipping.")
            continue

        seed = get_first(data_sources, "seed", 0)
        variants = get_first(data_sources, "variants")
        walkthrough = get_first(data_sources, "walkthrough")
        keep_source = get_first(data_sources, "keep_source", False)
        binary_name = get_first(data_sources, "binary_name", (name_prefix + "-" + cid) if name_prefix else cid)
        image = get_first(data_sources, "image", None) or get_first(data_sources, "build_image", None) or get_first(data_sources, "verify_image", None)
        attributes = get_first(data_sources, "attributes", {})

        if args.challenges and cid not in args.challenges and not any(cc.startswith(cid+":") for cc in args.challenges):
            continue

        for v in range(variants):
            if args.challenges and cid not in args.challenges and f"{cid}:{v}" not in args.challenges:
                continue

            chal_class = pwnshop.ALL_CHALLENGES[class_name]
            if attributes:
                chal_class = chal_class.duplicate_class(attributes=attributes)

            env = pwnshop.DockerEnvironment(image) if image else None

            challenge = chal_class(
                walkthrough=walkthrough,
                seed=seed + v,
                basename=binary_name,
                env=env,
                style=not args.no_style,
            )

            if args.debug_output:
                challenge._owns_workdir = False

            with background_runner, challenge:
                print(f"Applying {cid} variant {v} (of {variants}).")

                print(f"... instantiating {class_name}")

                out_dir = f"{yaml_dir}/{cid}/_{v}" if variants > 1 else f"{yaml_dir}/{cid}"
                if os.path.exists(out_dir):
                    shutil.copytree(out_dir, challenge.work_dir, dirs_exist_ok=True)
                else:
                    os.makedirs(out_dir)

                os.chdir(challenge.work_dir)

                if args.no_render and not args.no_build:
                    print("... using existing source")
                else:
                    print("... rendering")
                    challenge.render()

                if args.no_build:
                    print("... using existing binary")
                else:
                    print("... building")
                    challenge.build()

                if not args.no_verify:
                    print("... verifying")
                    challenge.flaky_verify()
                    print("... verification passed")

                if not args.no_deploy:
                    print(f"... deploying challenge to {out_dir}")
                    challenge.deploy(out_dir, bin=True, src=keep_source, libs=True)

                #if pdb:
                #   with open(f"{args.out.name.replace('.exe', '.pdb')}", 'wb') as f:
                #       f.write(pdb)

    ezmp.wait()

def main():
    parser = argparse.ArgumentParser(description="pwnshop challenge emitter", formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "-C",
        "--challenge-location",
        required=False,
        help="a path glob to import challenges from (either /path/to/module.py or /path/to/package/ or /some/glob/*, but avoid shell-expansion for the latter!). Defaults to cwd.",
        default=os.getcwd()
    )
    parser.add_argument(
        "--image",
        help="A docker image to use for building and verifying",
        default=None,
    )
    parser.add_argument(
        "-D",
        "--workdir",
        help="The working directory to use",
        default=None,
    )
    commands = parser.add_subparsers(help="the action for pwnshop to perform", required=True, dest="ACTION")
    command_render = commands.add_parser("list", help="list known challenges")
    command_render = commands.add_parser("render", help="render the source code of a challenge")
    command_build = commands.add_parser("build", help="build the binary code of a challenge")
    command_verify = commands.add_parser("verify", help="verify the functionality of a challenge")
    command_apply = commands.add_parser("apply", help="parse a yaml and generate the defined challenges")

    command_render.add_argument(
        "--line-numbers",
        action="store_true",
        help="render line numbers",
    )

    command_apply.add_argument(
        "--no-verify",
        action="store_true",
        help="Do not verify the challenge.",
    )
    command_apply.add_argument(
        "--no-build",
        action="store_true",
        help="Do not build the challenge (e.g., only verify).",
    )
    command_apply.add_argument(
        "--no-render",
        action="store_true",
        help="Do not re-render the code (will be ignored if no code is available).",
    )
    command_apply.add_argument(
        "--no-deploy",
        action="store_true",
        help="Do not deploy the built challenge.",
    )
    command_apply.add_argument(
        "--variants",
        type=int,
        help="Override the number of variants specified in the yaml (useful for testing).",
        default=1,
    )
    command_apply.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="When used with --mp, only produce output for failed builds.",
    )
    command_apply.add_argument(
        "--mp",
        action="store_true",
        help="Process challenges concurrently.",
    )
    command_apply.add_argument(
        "yaml",
        help="Path to the yaml.",
    )

    command_verify.add_argument(
        "--strace",
        action="store_true",
        help="print out strace information during verification",
    )

    command_verify.add_argument(
        "-f",
        "--flag",
        help="change the flag to be verified against",
        default="pwn.college{TESTFLAG.ehCUlFggVqD8JsUQin.0V.TESTFLAG}"
    )

    command_verify.add_argument(
        "--timeout",
        type=int,
        help="set a per-challenge timeout (in seconds) for verification",
    )

    command_verify.add_argument(
        "-m",
        "--module",
        help="Verify all the challenges in a module. Can be specified multiple times.",
        action="append"
    )

    command_verify.add_argument(
        "--build-image",
        help="Docker image to use for building",
        default=os.environ.get("BUILD_IMAGE", None)
    )

    command_verify.add_argument(
        "--verify-image",
        help="Docker image to use for verification",
        default=os.environ.get("VERIFY_IMAGE", None)
    )

    # common arguments
    for subparser in commands.choices.values():
        subparser.add_argument(
            "-s",
            "--seed",
            required=False,
            default=random.randrange(0, 999999),
            help="the seed from which to generate the challenge (default: random)",
        )

        subparser.add_argument(
            "--no-style",
            default=False,
            action="store_true",
            help="disable styling during template rendering",
        )

        subparser.add_argument(
            "-d",
            "--debug-output",
            action="store_true",
            help="print out debugging information",
        )

        subparser.add_argument(
            "-g",
            "--debug-symbols",
            action="store_true",
            help="compile with debug symbols",
        )

        subparser.add_argument(
            "--walkthrough",
            action="store_true",
            help="enable challenge walkthrough mode",
        )

    # common to all single-challenge commands
    for subparser in [ command_render, command_build, command_verify, command_apply ]:
        subparser.add_argument("challenges", help="the challenges, as multiple ChallengeClassName or ModuleName:level_number. Default: all challenges.", nargs="*")

    parser.epilog = f"""Commands usage:\n\t{command_render.format_usage()}\t{command_build.format_usage()}\t{command_verify.format_usage()}"""

    args = parser.parse_args()
    pwnlib.context.context.log_level = "ERROR"

    import_dir = args.challenge_location
    if not os.path.isdir(import_dir):
        print(f"Error, {import_dir=} does not exist")
        return -1
    imports = glob.glob(import_dir)
    for i in imports:
        i = i.rstrip("/")
        sys.path.append(os.path.realpath(os.path.dirname(i)))
        try:
            module_name = os.path.basename(i).split(".py")[0]
            __import__(module_name)
        finally:
            sys.path.pop()

    if args.workdir:
        os.makedirs(args.workdir, exist_ok=True)

    r = globals()["handle_" + args.ACTION.replace('-', '_')](args)
    if r in (None, True):
        return 0
    elif type(r) is int:
        return r
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())
