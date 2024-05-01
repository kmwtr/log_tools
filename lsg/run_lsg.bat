rem /d（ドライブの変更。Dに）
rem %0（引数。0はバッチファイル自身）
rem ~dp（引数の文字列を任意の形に整形する。%0をドライブ文字とパスだけに展開）

cd /d %~dp0

rem 実行。
rem %*（引数。すべての引数）

python lsg.py %*

rem pause