set --local alias_path "alias.toml"
set --local relation_path "relations.toml"
set --local cache_dir "relations.toml"
set --local cache_permanent "cache_permanent.toml"

rm -f alias_path relation_path cache_dir

alias mb "mbib --alias-file $alias_path --relation-file $relation_path"

echo "Adding aliases example.tex"
mb alias add Hoc2014 arxiv:1212.1873
mb alias add HocShm2012 zbl:1251.28008
mb alias add Shm2019 doi:10.4007/annals.2019.189.2.1
mb alias add to_delete something-false
mb alias add to_delete zbl:00.00
mb alias list
echo

echo "Generating example.tex"
mb generate example.tex
echo

echo "Getting canonical"
mb get key Hoc2014
