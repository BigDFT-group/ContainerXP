VARS_OPT="SHORT_ARG LONG_ARG DEFAULT HELP"
INDENT='    '

uniopt() 
{
NAME=$1
ALL_OPTIONS="$ALL_OPTIONS $NAME"
i=1
for OPT in $VARS_OPT; do
   i=$((i+1))
   eval ${NAME}_${OPT}=\${${i}}
done
}

option_default() #name default
{
case $2 in
  ASSUME_YES|ASSUME_NO)
  prefix=ASSUME_
  default=${2#"$prefix"}
  echo $1=$default
  ;;
  *)
  echo $1=$2
  ;;
esac
}

option_case() # name short long default
{
case $4 in
  ASSUME_YES|ASSUME_NO)
  echo "-$2|--$3)"
  prefix=ASSUME_
  default=${4#"$prefix"}
  case $default in
     YES)
     echo "$INDENT" $1=NO
     ;;
     NO)
     echo "$INDENT" $1=YES
     ;;
  esac
  echo "$INDENT" shift
  echo "$INDENT" ";;"
  ;;
  *)
  echo "-$2)"
  echo "$INDENT" $1='"$2"'
  echo "$INDENT" shift
  echo "$INDENT" shift
  echo "$INDENT" ";;"
  echo "--$3=*)"
  echo "$INDENT" $1='"${key#*=}"'
  echo "$INDENT" shift
  echo "$INDENT" ";;"
  ;;
esac
}

option_help() #short long default help_string
{
	echo "$INDENT" echo '"' "-$1, --$2= (default: $3)" '"'
	echo "$INDENT" echo '"' "   " $4 '"'
}


get_suboptions()
{
for SUBNAME in $VARS_OPT; do
eval $SUBNAME=\$${1}_${SUBNAME}
done
}

build_case()
{
echo 'POSITIONAL=""'
echo 'while test $# -gt 0'
echo do
echo 'key="$1"'
echo 'case "$key" in'
echo '-h|--help)'
for NAME in $ALL_OPTIONS; do
	get_suboptions $NAME
	option_help $SHORT_ARG $LONG_ARG "$DEFAULT" "$HELP"
done
echo "$INDENT" shift
echo "$INDENT" ";;"
for NAME in $ALL_OPTIONS; do
	get_suboptions $NAME
	option_case $NAME $SHORT_ARG $LONG_ARG "$DEFAULT"
done
echo "*)    # unknown option"
echo "$INDENT" 'POSITIONAL="$POSITIONAL $1" # save it in a sequence for later'
echo "$INDENT" 'shift # past argument'
echo "$INDENT" ';;'
echo esac
echo done
}

set_default()
{
for NAME in $ALL_OPTIONS; do
        get_suboptions $NAME
	option_default $NAME "$DEFAULT"
done
} 

final_values()
{
for NAME in $ALL_OPTIONS; do
   echo echo $NAME=\$$NAME
done
echo echo "POSITIONAL=\$POSITIONAL"
}

parser_code()
{
echo '#----'
set_default
build_case
if test "x"$UNIOPT_VERBATIM = "x1"; then
	final_values
fi
echo '#----'
}

uniopt_parser()
{
	if test "x"$UNIOPT_VERBATIM = "x1"; then
		parser_code
	fi
	tmpfile=$PWD/uniopt_tmpfile.sh
	parser_code > $tmpfile
	. "$tmpfile" $@
	rm -f $tmpfile
}

