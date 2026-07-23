# 卒業論文ビルド用 Makefile
# 設定は .latexmkrc に集約（lualatex + bibtex）。ここではワークフローだけ定義する。

MAIN := main
LATEXMK := latexmk

.PHONY: all build watch clean distclean view

all: build

# PDF をビルド（.latexmkrc の設定を使用）
build:
	$(LATEXMK) $(MAIN).tex

# ソース変更を監視して自動リビルド
watch:
	$(LATEXMK) -pvc $(MAIN).tex

# 中間ファイルを削除（PDF は残す）
clean:
	$(LATEXMK) -c

# 中間ファイルと PDF をすべて削除
distclean:
	$(LATEXMK) -C

# ビルドして PDF を開く
view:
	$(LATEXMK) -pv $(MAIN).tex
