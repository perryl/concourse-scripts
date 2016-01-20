def transform_upstream_prefix: if contains("upstream") then "delta" else "baserock" end;

def chunk_to_resource: {name: .name, type: "git", source: {uri: "http://git.baserock.org/\(.repo | transform_upstream_prefix)/\(.name)", branch: ."unpetrify-ref"}};

def strata_to_resources: .chunks | [.[] | chunk_to_resource];

def chunk_to_get: {get: .name, resource: .name, trigger: true};

def strata_to_plan: {aggregate: [.chunks | .[] | chunk_to_get]}; 

def strata_to_job: {name: .name, public: true, plan: strata_to_plan, resources: strata_to_resources};
strata_to_job
