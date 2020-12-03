bash bin/bundle_js.sh
echo $(date "+%s") >> app/build_time
service apache2 restart
