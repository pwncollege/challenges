#include <assert.h>
#include <err.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <checkpoint.h>

static int play_round(int player)
{
    static int wins;
    const char *moves[] = {"rock", "paper", "scissors"};
    int opponent = rand() % 3;
    printf("%s vs %s: ", moves[player], moves[opponent]);

    if ((player - opponent + 3) % 3 != 1) {
        wins = 0;
        puts(player == opponent ? "tie" : "loss");
    } else {
        printf("win (%d/10)\n", ++wins);
    }
    return wins;
}

int main(void)
{
    char history[11] = {0};
    setbuf(stdout, NULL);

    for (int round = 0; round < 10; round++) {
        long generation = checkpoint();
        assert(generation >= 0 && generation < 3);
        int wins = play_round(generation);
        if (wins == 0) {
            puts("Restoring...");
            restore();
            errx(1, "restore returned to its caller");
        }

        assert(wins == round + 1);
        history[round] = "RPS"[generation];
    }

    assert(strcmp(history, "SSPSRSSPPS") == 0);
    printf("Winning moves: %s\n", history);
    return 0;
}
