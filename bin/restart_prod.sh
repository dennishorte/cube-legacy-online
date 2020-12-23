echo "Restarting Cube Legacy Online"

echo "...storing build time"
echo $(date "+%s") >> app/build_time

echo "...building js bundle"
bash bin/bundle_js.sh

echo "...preprocessing sass"
bash bin/apply_sass.sh

echo "...restarting apache"
service apache2 restart
