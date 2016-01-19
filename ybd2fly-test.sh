x=$(python -c 'import sys, yaml, json; json.dump(yaml.load(sys.stdin), sys.stdout, indent=4)' < "$1" | jq ".")
strata=$(echo "$x" | jq -r ".strata | .[] | .morph")

for i in $strata; do
  a=$(python -c 'import sys, yaml, json; json.dump(yaml.load(sys.stdin), sys.stdout, indent=4)' < "$i" | jq ".")
  echo "$a" | jq '.chunks | resources: [.[] | {name: .name, type: "git", source: {uri: "http://git.baserock.org/\(.name)", branch: ."unpetrify-ref"}}]}'

done
