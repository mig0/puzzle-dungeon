# Common shell function library to be sourced

function generate_file {
	filename="$1"
	tmp_filename="$1.tmp"
	cat >"$tmp_filename"
	if test ! -f $filename -o "`cksum $filename $tmp_filename 2>/dev/null | cut -d' ' -f1 | sort -u | wc -l`" = 2; then
		mv $tmp_filename $filename
		echo "Generated new $filename"
	else
		rm "$tmp_filename"
		echo "File $filename was not changed"
	fi
}
