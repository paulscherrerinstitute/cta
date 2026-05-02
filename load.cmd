require seq

dbLoadTemplate("cta.template", "SYS=$(SYS), DEVICE=$(DEVICE), DN=$(DN), EOS=$(EOS), PIR=$(PIR)")


#seq &ctaSeq, "DN=$(DN):,EOS=$(EOS):"
