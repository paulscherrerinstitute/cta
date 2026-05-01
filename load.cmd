require seq

dbLoadTemplate("cta.template", "SYS=$(SYS), DEVICE=$(DEVICE), DN=$(DN), EOS=$(EOS), PIR=$(PIR)")


seq &ctaSeq, "P=$(SYS)-CCTA,EOS=$(EOS)"
