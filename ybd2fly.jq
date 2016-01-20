def transform_upstream_prefix: if contains("upstream") then "delta" else "baserock" end;

def chunk_to_resource: {name: .name, type: "git", source: {uri: "http://git.baserock.org/\(.repo | transform_upstream_prefix)/\(.name)", branch: ."unpetrify-ref"}};

def strata_to_resources: .chunks | {resources: [.[] | chunk_to_resource]};

strata_to_resources
