bash bin/bundle_js.sh
bash bin/apply_sass.sh
echo $(date "+%s") >> app/build_time
service apache2 restart
