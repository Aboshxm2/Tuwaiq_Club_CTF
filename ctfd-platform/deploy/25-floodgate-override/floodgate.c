/* Challenge 25 - Floodgate Override (deployable, raw TCP / pwn).
 *
 * A classic ret2win. vuln() reads far more than its stack buffer holds, so the
 * saved return address can be overwritten with the address of win(). win() is
 * never called on the normal path; it prints the flag from the FLAG env var.
 *
 * Built with -fno-stack-protector -no-pie, so win() has a fixed address and
 * there is no canary. Symbols are kept on purpose: this is an introductory
 * challenge, so `win` is easy to find in a decompiler.
 *
 * Intended solve (organizer note): payload = b"A"*72 + p64(&win). The 72-byte
 * offset is buf[64] + the saved rbp (8). The flag is provided per team by whale
 * in the FLAG env var and is not present in the binary.
 */
#include <unistd.h>
#include <stdlib.h>
#include <string.h>

static void out(const char *s) { write(1, s, strlen(s)); }

void win(void) {
    char *flag = getenv("FLAG");
    out("\n[FLOODGATES OPEN] override accepted:\n");
    if (flag) write(1, flag, strlen(flag));
    out("\n");
    _exit(0);
}

void vuln(void) {
    char buf[64];
    out("Enter the 32-character override code: ");
    read(0, buf, 512); /* overflow: reads up to 512 bytes into a 64-byte buffer */
    out("ACCESS DENIED\n");
}

int main(void) {
    out("=== Oasis Dam - Floodgate Control Terminal ===\n");
    out("Unauthorized access is prohibited.\n");
    vuln();
    return 0;
}
