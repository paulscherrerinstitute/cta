program ctaSeq

int sos;
int s1_proc;
int s2_proc;
evflag sosFlag;

assign sos to     "{DN}:seq0Ctrl-SOS-I";
assign s1_proc to "{EOS}:Seq1-Do-I";
assign s2_proc to "{EOS}:Seq2-Do-I";

monitor sos;
sync sos sosFlag;

ss main {
    state idle {
        when(efTestAndClear(sosFlag)) {
            s1_proc=1;
            pvPut(s1_proc);
        } state idle
    }
}
