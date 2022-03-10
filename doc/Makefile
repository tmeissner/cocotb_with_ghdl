DOC := qz2021_-_using_python_for_verification_of_digital_systems.md

PDF := $(DOC:.md=.pdf)

.PHONY: all
all: $(PDF)

%.pdf: %.md template/template.tex images/*
	pandoc -t beamer --pdf-engine xelatex --listings --template=template/template.tex $< -o $@

.PHONY: clean
clean:
	rm -rf $(PDF)
