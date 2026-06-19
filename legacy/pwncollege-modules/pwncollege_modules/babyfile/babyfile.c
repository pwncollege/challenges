{% extends "base/base.c" %}

{% block globals %}
    FILE *fp;
    {% if challenge.schema == "tutorial" %}
        char *buf;
    {% endif %}
    {% if challenge.hidden_flag %}
        char secret[100];
    {% endif %}
    {% if challenge.authenticate %}
        int authenticated;
    {% endif %}

    void create_tmp_file() {
	    umask(00000);
	    int fd = open("/tmp/babyfile.txt", O_WRONLY | O_CREAT, 0666);
	    write(fd, "FLAG{NOT_HAPPENING}\n", 20);
	    close(fd);
        {% if challenge.babyflag %}
	    fd = open("/tmp/babyflag.txt", O_WRONLY | O_CREAT, 0600);
	    int flag_fd = open("/flag", O_RDONLY);
	    sendfile(fd, flag_fd, 0, 0x100);
	    close(fd);
	    close(flag_fd);
	{% endif %}
    }

    {% if walkthrough %}
        void print_fp(FILE *fp) {
            printf("Here is the contents of the FILE structure.\n");
            printf("fp -> %p\n", fp);
            printf("0x00\t_flags \t\t\t*%p = 0x%x\n", &(fp->_flags), fp->_flags);
            printf("0x08\t_IO_read_ptr \t\t*%p = %p\n", &(fp->_IO_read_ptr), fp->_IO_read_ptr);
            printf("0x10\t_IO_read_end \t\t*%p = %p\n", &(fp->_IO_read_end), fp->_IO_read_end);
            printf("0x18\t_IO_read_base \t\t*%p = %p\n", &(fp->_IO_read_base), fp->_IO_read_base);
            printf("0x20\t_IO_write_base \t\t*%p = %p\n", &(fp->_IO_write_base), fp->_IO_write_base);
            printf("0x28\t_IO_write_ptr \t\t*%p = %p\n", &(fp->_IO_write_ptr), fp->_IO_write_ptr);
            printf("0x30\t_IO_write_end \t\t*%p = %p\n", &(fp->_IO_write_end), fp->_IO_write_end);
            printf("0x38\t_IO_buf_base \t\t*%p = %p\n", &(fp->_IO_buf_base), fp->_IO_buf_base);
            printf("0x40\t_IO_buf_end \t\t*%p = %p\n", &(fp->_IO_buf_end), fp->_IO_buf_end);
            printf("0x48\t_IO_save_base \t\t*%p = %p\n", &(fp->_IO_save_base), fp->_IO_save_base);
            printf("0x50\t_IO_backup_base \t*%p = %p\n", &(fp->_IO_backup_base), fp->_IO_backup_base);
            printf("0x58\t_IO_save_end \t\t*%p = %p\n", &(fp->_IO_save_end), fp->_IO_save_end);
            printf("0x60\t_markers \t\t*%p = %p\n", &(fp->_markers), fp->_markers);
            printf("0x68\t_chain \t\t\t*%p = %p\n", &(fp->_chain), fp->_chain);
            printf("0x70\t_fileno \t\t*%p = %d\n", &(fp->_fileno), fp->_fileno);
            printf("0x74\t_flags2 \t\t*%p = %d\n", &(fp->_flags2), fp->_flags2);
            printf("0x78\t_old_offset \t\t*%p = %ld\n", &(fp->_old_offset), fp->_old_offset);
            printf("0x80\t_cur_column \t\t*%p = %hd\n", &(fp->_cur_column), fp->_cur_column);
            printf("0x82\t_vtable_offset \t\t*%p = %hhd\n", &(fp->_vtable_offset), fp->_vtable_offset);
            printf("0x83\t_shortbuf \t\t*%p = %hhd\n", &(fp->_shortbuf), fp->_shortbuf);
            printf("0x88\t_lock \t\t\t*%p = %p\n", &(fp->_lock), fp->_lock);

            printf("0x90\t_offset \t\t*%p = %ld\n", &(fp->_offset), fp->_offset);
            printf("0x98\t_codecvt \t\t*%p = %p\n", &(fp->_codecvt), fp->_codecvt);
            printf("0xa0\t_wide_data \t\t*%p = %p\n", &(fp->_wide_data), fp->_wide_data);
            printf("0xa8\t_freeres_list \t\t*%p = %p\n", &(fp->_freeres_list), fp->_freeres_list);
            printf("0xb0\t_freeres_buf \t\t*%p = %p\n", &(fp->_freeres_buf), fp->_freeres_buf);
            printf("0xb8\t__pad5 \t\t\t*%p = %ld\n", &(fp->__pad5), fp->__pad5);
            printf("0xc0\t_mode \t\t\t*%p = %d\n", &(fp->_mode), fp->_mode);
            long int unusedsize = 15 * sizeof (int) - 4 * sizeof (void *) - sizeof (size_t);
            printf("0xc4\t_unused2[%ld] \t\t*%p = {", unusedsize, &(fp->_unused2));
            for(int i = 0; i < unusedsize - 1; i++) {
                printf("%hhx:", fp->_unused2[i]);
            }
            printf("%hhx}\n", fp->_unused2[unusedsize - 1]);
        }
    {% endif %}

    {% if challenge.auth_function %}
        void authenticate(
            {% if challenge.password %}
                char *password
            {% endif %}
            )
        {
            {% if challenge.password %}
                int canary = 0x42424242;
            {% endif %}
            {% if challenge.password %}
            if (!strcmp(password, "password"))
            {
            {% endif %}
                static char flag[256];
                static int flag_fd;
                static int flag_length;
                
                chmod("/flag", 0777);
                printf("You win! Here is your flag:\n");
                flag_fd = open("/flag", 0);
                if (flag_fd < 0)
                {
                    printf("\n  ERROR: Failed to open the flag -- %s!\n", strerror(errno));
                    if (geteuid() != 0)
                    {
                        printf("  Your effective user id is not 0!\n");
                        printf("  You must directly run the suid binary in order to have the correct permissions!\n");
                    }
                    return;
                }
                flag_length = read(flag_fd, flag, sizeof(flag));
                if (flag_length <= 0)
                {
                    printf("\n  ERROR: Failed to read the flag -- %s!\n", strerror(errno));
                    return;
                }
                {% if challenge.password %}
                if (canary == 0x42424242)
                {
                {% endif %}
                    write(1, flag, flag_length);
                    printf("\n\n");
                {% if challenge.password %}
                }
                else
                {
                    printf("No cheating!\n");
                    exit(0);
                }
                {% endif %}
            {% if challenge.password %}
            }
            else
            {
                printf("You are not 1337 enough.");
                exit(0);
            }
            {% endif %}
        }
    {% endif %}
{% endblock %}

{% block challenge_function %}
    {% if challenge.schema == "notesapp" %}
        char *notes[{{ challenge.notes_count }}] = { 0 };
        unsigned int notes_sizes[{{ challenge.notes_count }}] = { 0 };
        char cmd[128];
        unsigned int index;
        unsigned int size;
    {% endif %}

    {% if challenge.schema == "tutorial" %}
	create_tmp_file();
        {% if challenge.leak_stack %}
            int stack_number;
            printf("[LEAK] return address is stored at: 0x%llx\n", ((long long int)&stack_number)+0x14);
        {% endif %}
        {% if challenge.leak_fp %}
            printf("[LEAK] You will be writing to 0x%llx within the file pointer\n", (long long int)fp + {{ challenge.write_offset }});
        {% endif %}
        {% if challenge.authenticate %}
            authenticated = 0;
        {% endif %}
        buf = malloc(0x100);
        {% if challenge.leak_buf %}
            printf("[LEAK] The name buffer is located at: %p\n", buf);
        {% endif %}
        {% if challenge.rw %}
            {% if walkthrough %}
                {% filter layout_text_walkthrough %}
                    This exploit will involve altering the flow of data by editing
                    the _fileno attribute of a FILE structure so that private data
                    can be made publicly readable.
                {% endfilter %}
            {% endif %}
            fp = fopen("{{ challenge.file_path }}", "r+");
        {% elif challenge.fread %}
            {% if walkthrough %}
                {% filter layout_text_walkthrough %}
                    This exploit will involve performing an arbitrary write
                    to execute a code segment which is otherwise unreachable.
                {% endfilter %}
            {% endif %}
            fp = fopen("{{ challenge.file_path }}", "r");
        {% elif challenge.fwrite %}
            {% if walkthrough %}
                {% if challenge.win_function or challenge.auth_function %}
                    {% filter layout_text_walkthrough %}
                        This exploit will involve altering the virtual function table
                        to directly hijack control flow to execute the win function hidden
                        in this executable. This can be done by creating a fake _wide_data struct
                        which will not have a security check on the vtable. This wide data struct
                        may or may not be overlapping with the original FILE struct. Not overlapping
                        these may be easier to understand but may be harder since you will need access to more memory.
                        In addition to hijacking control flow, you can also control the first parameter since the virtual
                        functions are called with FUNC(fp). By controlling contents of the FILE structure, you can control
                        the next function call and its first parameter.
                    {% endfilter %}
                {% else %}
                    {% filter layout_text_walkthrough %}
                        This exploit will involve performing an arbitrary read
                        to leak some sensitive the flag.
                    {% endfilter %}
                {% endif %}
            {% endif %}
            fp = fopen("{{ challenge.file_path }}", "w");
        {% elif challenge.write_stdout %}
            {% if walkthrough and challenge.auth_function %}
                {% filter layout_text_walkthrough %}
                    This FILE struct points to _IO_2_1_stdout_ (otherwise known as just stdout).
                    The stdout FILE struct also has a virtual function table which can be abused.
                    Just like any other virtual function table, you can hijack control flow and also
                    control the first parameter, if needed.
                {% endfilter %}
            {% elif walkthrough %}
                {% filter layout_text_walkthrough %}
                    This FILE struct points to _IO_2_1_stdout_ (otherwise known as just stdout).
                    The stdout FILE struct can be abused to perform arbitrary read exploits.
                    These exploits will be triggered by functions such as puts() or printf()
                {% endfilter %}
            {% endif %}
            fp = stdout;
        {% elif challenge.write_stdin %}
            {% if walkthrough %}
                {% filter layout_text_walkthrough %}
                    This FILE struct points to _IO_2_1_stdin_ (otherwise known as just stdin)
                    The stdin FILE struct can be abused to perform arbitrary write exploits.
                    These exploits will be triggered by functions such as scanf().
                {% endfilter %}
            {% endif %}
            fp = stdin;
        {% elif challenge.write_stderr %}
            {% if walkthrough %}
                {% filter layout_text_walkthrough %}
                This FILE struct points to _IO_2_1_stderr_ (otherwise known as just stderr)
                {% endfilter %}
            {% endif %}
            fp = stderr;
        {% endif %}

        {% if challenge.read_flag %}
            fread(buf, 1, 0x100, fp);
            FILE *fp2 = fopen("/tmp/babyfile.txt", "r+");
            {% if walkthrough %}
                printf("fp2->_fileno = %d\n", fp2->_fileno);
            {% endif %}
        {% endif %}

        {% if walkthrough %}
            print_fp(fp);
        {% endif %}

        {% if challenge.write_buf %}
            puts("Please enter your name.");
            read(0, buf, 0x100);
            printf("Hello, %s!\n", buf);
        {% endif %}

        {% if walkthrough %}
            {% filter layout_text_walkthrough %}
                Now reading from stdin directly to the FILE struct.
            {% endfilter %}
        {% endif %}


        {% if challenge.leak_fp %}
            printf("[LEAK] You are writing to: 0x%llx\n", (long long int)fp + {{ challenge.write_offset }});
        {% endif %}
        {% if challenge.write_fp %}
            read(0, (long long int)fp + {{ challenge.write_offset }}, 0x1e0 - {{ challenge.write_offset }});
        {% endif %}
        
        {% if walkthrough %}
            print_fp(fp);
        {% endif %}

        {% if challenge.fread and not challenge.read_flag %}
            fread(buf, sizeof(char), 0x100, fp);
        {% elif challenge.fwrite or challenge.read_flag %}
            fwrite(buf, sizeof(char), 0x100, fp);
        {% elif challenge.rw %}
            fread(buf, sizeof(char), 0x100, fp);
            {% if walkthrough %}
                print_fp(fp);
            {% endif %}
            read(0, (long long int)fp + {{ challenge.write_offset }}, 0x1e0 - {{ challenge.write_offset }});
            {% if walkthrough %}
                print_fp(fp);
            {% endif %}
            fwrite(buf, sizeof(char), 0x100, fp);
        {% endif %}

        {% if challenge.authenticate %}
            {% if challenge.write_stdin %}
                puts("Please log in.");
                scanf("%64s", buf);
            {% endif %}
            if (authenticated) {
                win();
            }
            else {
                puts("You are not 1337 enough.");
            }
        {% endif %}

    {% elif challenge.schema == "notesapp" %}
	create_tmp_file();
        {% if challenge.leak_stack %}
            printf("[LEAK] The address of cmd where you are writing to is: %p\n\n", &cmd);
        {% endif %}
        while (true) {
            printf("[*] Commands: ({{ challenge.functions_description }}):\n> ");
            scanf("%127s%*c", cmd);
            puts("");
            if (!strcmp(cmd, "new_note")) {
                {% if challenge.notes_count > 1 %}
                    printf("Which note? (0-{{ challenge.notes_count }})\n> ");
                    scanf("%127s%*c", cmd);
                    index = atoi(cmd);
                {% else %}
                    index = 0;
                {% endif %}
                printf("How many bytes to the note?\n> ");
                scanf("%127s%*c", cmd);
                size = atoi(cmd);
                notes[index] = malloc(size);
                notes_sizes[index] = size;
                {% if walkthrough %}
                    printf("notes[%d] = %p;", index, notes[index]);
                {% endif %}
            }
            {% if "del_note" in challenge.functions %}
            else if (!strcmp(cmd, "del_note")) {
                {% if challenge.notes_count > 1 %}
                    printf("Which note? (0-{{ challenge.notes_count }})\n> ");
                    scanf("%127s%*c", cmd);
                    index = atoi(cmd);
                {% else %}
                    index = 0;
                {% endif %}
                {% if walkthrough %}
                    printf("free(notes[%d]);\n", index);

                {% endif %}
                free(notes[index]);
                notes[index] = NULL;
            }
            {% endif %}
            {% if "write_note" in challenge.functions %}
            else if (!strcmp(cmd, "write_note")) {
                {% if challenge.notes_count > 1 %}
                    printf("Which note? (0-{{ challenge.notes_count }})\n> ");
                    scanf("%127s%*c", cmd);
                    index = atoi(cmd);
                    read(0, notes[index], notes_sizes[index]);
                {% else %}
                    read(0, notes[0], notes_sizes[0]);
                {% endif %}
            }
            {% endif %}
            {% if "read_note" in challenge.functions %}
            else if (!strcmp(cmd, "read_note")) {
                {% if challenge.notes_count > 1 %}
                    printf("Which note? (0-{{ challenge.notes_count }})\n> ");
                    scanf("%127s%*c", cmd);
                    index = atoi(cmd);
                    read(1, notes[index], notes_sizes[index]);
                {% else %}
                    write(1, notes[0], notes_sizes[0]);
                {% endif %}
            }
            {% endif %}
            {% if "open_file" in challenge.functions %}
            else if (!strcmp(cmd, "open_file")) {
                {% if "write_file" in challenge.functions and "read_file" in challenge.functions %}
                    fp = fopen("{{ challenge.file_path }}", "r+");
                    {% if walkthrough %}
                        printf("fp = fopen(\"{{ challenge.file_path }}\", \"r+\") = %p\n", fp);
                    {% endif %}
                {% elif "write_file" in challenge.functions %}
                    fp = fopen("{{ challenge.file_path }}", "w");
                    {% if walkthrough %}
                        printf("fp = fopen(\"{{ challenge.file_path }}\", \"w\") = %p\n", fp);
                    {% endif %}
                {% elif "read_file" in challenge.functions %}
                    fp = fopen("{{ challenge.file_path }}", "r");
                    {% if walkthrough %}
                        printf("fp = fopen(\"{{ challenge.file_path }}\", \"r\") = %p\n", fp);
                    {% endif %}
                {% endif %}
            }
            {% endif %}
            {% if "close_file" in challenge.functions %}
            else if (!strcmp(cmd, "close_file")) {
                fclose(fp);
            }
            {% endif %}
            {% if "write_file" in challenge.functions %}
            else if (!strcmp(cmd, "write_file")) {
                {% if challenge.notes_count > 1 %}
                    printf("Which note? (0-{{ challenge.notes_count }})\n> ");
                    scanf("%127s%*c", cmd);
                    index = atoi(cmd);
                {% else %}
                    index = 0;
                {% endif %}
                {% if walkthrough %}
                    printf("fwrite(notes[%d], %d, %d, fp);\n", index, sizeof(char), notes_sizes[index]);
                {% endif %}
                fwrite(notes[index], sizeof(char), notes_sizes[index], fp);
            }
            {% endif %}
            {% if "read_file" in challenge.functions %}
            else if (!strcmp(cmd, "read_file")) {
                {% if challenge.notes_count > 1 %}
                    printf("Which note? (0-{{ challenge.notes_count }})\n> ");
                    scanf("%127s%*c", cmd);
                    index = atoi(cmd);
                {% else %}
                    index = 0;
                {% endif %}
                {% if walkthrough %}
                    printf("fread(notes[%d], %d, %d, fp);\n", index, sizeof(char), notes_sizes[index]);
                {% endif %}
                fread(notes[index], sizeof(char), notes_sizes[index], fp);
            }
            {% endif %}
            {% if "write_fp" in challenge.functions %}
            else if (!strcmp(cmd, "write_fp")) {
                {% if walkthrough %}
                    print_fp(fp);
                {% endif %}
                read(0, fp, 0x1e0);
                {% if walkthrough %}
                    print_fp(fp);
                {% endif %}
            }
            {% endif %}
            {% if "open_flag" in challenge.functions %}
            else if (!strcmp(cmd, "open_flag")) {
                FILE *flagfile = fopen("/tmp/babyflag.txt", "r+");
            }
            {% endif %}
            {% if challenge.authenticate %}
            else if (!strcmp(cmd, "authenticate")) {
                if (authenticated) {
                    win();
                }
                else {
                    printf("You are not 1337 enough.\n");
                }
            }
            {% endif %}
            else if (!strcmp(cmd, "quit")) {
                break;
            }
            else {
                puts("Unrecognized choice!\n");
            }

        }
    {% endif %}
{% endblock %}

{% block main %}
    {% if walkthrough %}
        {% filter layout_text_walkthrough %}
            This challenge allows you to manipulate the memory of an _IO_FILE struct object.
            By doing this, you can arbitrarily read or write to take control of the process.
            You may also take control of the virtual function table at the end of the FILE struct.
            If you do this, then you can directly take control of the process and call some other function.
        {% endfilter %}
    {% endif %}
    
    {% if challenge.hidden_flag %}
        {% if walkthrough %}
            printf("The flag has been read into memory and is located at %p\n", secret);
        {% endif %}
        read(open("/flag", 0), secret, 100);
    {% endif %}
    {% if challenge.leak_pie %}
        printf("[LEAK] main is located at: %p\n", main);
    {% endif %}
    {% if challenge.leak_libc %}
        printf("[LEAK] The address of puts() within libc is: %p\n\n", puts);
    {% endif %}
{% endblock %}
