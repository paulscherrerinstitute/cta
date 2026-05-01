program ctaSeq

int sos;
int s1_proc;

assign sos to     "{P}SOS-I";
assign s1_proc to "{EOS}Seq1-Do-I";

monitor sos;

ss main {
    state idle {
        when(sos) {
            printf("sos received");
            s1_proc=1;
            pvPut(s1_proc);
        } state idle
    }
}
