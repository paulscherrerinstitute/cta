program ctaSeq

int sos;
int cur;
int s1_proc;
int s2_proc;
evflag sosFlag;

assign sos     to "{DN}seq0Ctrl-SOS-I";
assign cur     to "{DN}CurrSeq";
assign s1_proc to "{EOS}Seq1-Do-I.PROC";
assign s2_proc to "{EOS}Seq2-Do-I.PROC";

monitor sos;
monitor cur;

sync sos sosFlag;

ss main {

state idle {

    when (efTestAndClear(sosFlag)) {

        /* read which sequence just ran */
        pvGet(cur);  
        printf("SOS, cur=%d\n", cur);

        if (cur == 1) {
            /* S1 just ran → prepare S2 */
            s2_proc = 1;
            pvPut(s2_proc);
        } 

        else {
            /* S2 just ran → prepare S1 */
            s1_proc = 1;
            pvPut(s1_proc);
        }

    } state idle

}
}
