yaml_to_json () {
  python -c 'import sys, yaml, json; json.dump(yaml.load(sys.stdin), sys.stdout, indent=4)' < "$1" | jq "."
}

x=$(yaml_to_json "$1")
strata=$(echo "$x" | jq -r ".strata | .[] | .morph")

for i in $strata; do
  a=$(yaml_to_json "$i")
  echo "$a" | jq -f ybd2fly.jq | json2yaml
done
