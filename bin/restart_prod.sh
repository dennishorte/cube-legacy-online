bash bin/bundle_js.sh
echo $(date -j -f "%a %b %d %T %Z %Y" "`date`" "+%s") >> build_time
service apache2 restart
