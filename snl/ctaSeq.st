program ctaSeq

int SOS;

assign SOS to "$(P)SOS-I";
monitor SOS;

ss main {
    state idle {
        when(SOS) {
            printf("SOS received, value = %d\n", SOS);
        } state idle
    }
}
