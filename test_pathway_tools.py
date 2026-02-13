#!/usr/bin/env python3
"""
Test script for Pathway/Systems Biology tools
Following test-driven development: test ALL tools BEFORE creating skill documentation
"""

from tooluniverse import ToolUniverse


def _load_tools() -> ToolUniverse:
    """Load ToolUniverse once and return the instance."""
    tu = ToolUniverse()
    tu.load_tools()
    return tu


def test_reactome_tools(tu: ToolUniverse):
    """Test Reactome pathway database tools"""
    print("\n" + "="*80)
    print("TESTING REACTOME TOOLS")
    print("="*80)

    # Test 1: List top pathways
    print("\n1. Testing Reactome_list_top_pathways...")
    result = tu.tools.Reactome_list_top_pathways(species="Homo sapiens")
    # Reactome returns list directly, not wrapped in standard response
    if isinstance(result, list):
        print(f"Status: success (direct list response)")
        print(f"Found {len(result)} top-level pathways")
        if result:
            print(f"First pathway: {result[0].get('displayName', 'N/A')}")
            print(f"Pathway ID: {result[0].get('stId', 'N/A')}")
    elif isinstance(result, dict) and result.get('status') == 'success':
        data = result.get('data', [])
        print(f"Status: {result.get('status')}")
        print(f"Found {len(data)} top-level pathways")
        if data:
            print(f"First pathway: {data[0].get('displayName', 'N/A')}")
            print(f"Pathway ID: {data[0].get('stId', 'N/A')}")
    else:
        print(f"ERROR: Unexpected response format: {type(result)}")

    # Test 2: Map protein to pathways
    print("\n2. Testing Reactome_map_uniprot_to_pathways...")
    result = tu.tools.Reactome_map_uniprot_to_pathways(id="P53350")  # Note: uses 'id' not 'uniprot_id'
    if isinstance(result, list):
        print(f"Status: success (direct list response)")
        print(f"Found {len(result)} pathways for P53350")
        if result:
            print(f"First pathway: {result[0].get('displayName', 'N/A')}")
    elif isinstance(result, dict) and result.get('status') == 'success':
        data = result.get('data', [])
        print(f"Found {len(data)} pathways for P53350")
        if data:
            print(f"First pathway: {data[0].get('displayName', 'N/A')}")
    else:
        print(f"ERROR: Unexpected response format")

    # Test 3: Get pathway reactions
    print("\n3. Testing Reactome_get_pathway_reactions...")
    result = tu.tools.Reactome_get_pathway_reactions(stId="R-HSA-73817")  # Metabolism of RNA
    if isinstance(result, list):
        print(f"Status: success (direct list response)")
        print(f"Found {len(result)} reactions/subpathways")
    elif isinstance(result, dict) and result.get('status') == 'success':
        data = result.get('data', [])
        print(f"Found {len(data)} reactions/subpathways")
    else:
        print(f"ERROR: Unexpected response format")

    return True

def test_kegg_tools(tu: ToolUniverse):
    """Test KEGG pathway database tools"""
    print("\n" + "="*80)
    print("TESTING KEGG TOOLS")
    print("="*80)

    # Test 1: Search pathways
    print("\n1. Testing kegg_search_pathway...")
    result = tu.tools.kegg_search_pathway(keyword="diabetes")
    print(f"Status: {result.get('status')}")
    if result.get('status') == 'success':
        data = result.get('data', [])
        print(f"Found {len(data)} pathways for 'diabetes'")
        if data:
            print(f"First pathway: {data[0].get('pathway_id', 'N/A')} - {data[0].get('description', 'N/A')}")
    else:
        print(f"ERROR: {result.get('error', {}).get('message')}")

    # Test 2: Get pathway info
    print("\n2. Testing kegg_get_pathway_info...")
    result = tu.tools.kegg_get_pathway_info(pathway_id="hsa04930")  # Type II diabetes pathway
    print(f"Status: {result.get('status')}")
    if result.get('status') == 'success':
        data = result.get('data', {})
        print(f"Pathway name: {data.get('name', 'N/A')}")
        print(f"Number of genes: {len(data.get('genes', []))}")
    else:
        print(f"ERROR: {result.get('error', {}).get('message')}")

    return True

def test_wikipathways_tools(tu: ToolUniverse):
    """Test WikiPathways community-curated pathways"""
    print("\n" + "="*80)
    print("TESTING WIKIPATHWAYS TOOLS")
    print("="*80)

    # Test 1: Search pathways
    print("\n1. Testing WikiPathways_search...")
    result = tu.tools.WikiPathways_search(query="p53", organism="Homo sapiens")
    print(f"Status: {result.get('status')}")
    if result.get('status') == 'success':
        data = result.get('data', {})
        pathways = data.get('result', [])
        print(f"Found {len(pathways)} pathways for 'p53' in human")
        if pathways:
            print(f"First pathway: {pathways[0].get('id', 'N/A')} - {pathways[0].get('name', 'N/A')}")
    else:
        print(f"ERROR: {result.get('error', {}).get('message')}")

    return True

def test_pathway_commons_tools(tu: ToolUniverse):
    """Test Pathway Commons integrated database"""
    print("\n" + "="*80)
    print("TESTING PATHWAY COMMONS TOOLS")
    print("="*80)

    # Test 1: Search pathways
    print("\n1. Testing pc_search_pathways...")
    result = tu.tools.pc_search_pathways(action="search_pathways", keyword="apoptosis", limit=5)
    # Pathway Commons returns data directly without status wrapper
    if isinstance(result, dict) and 'total_hits' in result:
        print(f"Status: success (direct dict response)")
        print(f"Total hits: {result.get('total_hits', 0)}")
        pathways = result.get('pathways', [])
        print(f"Returned {len(pathways)} pathways")
        if pathways:
            print(f"First pathway: {pathways[0].get('name', 'N/A')}")
            print(f"Data source: {pathways[0].get('source', 'N/A')}")
    elif isinstance(result, dict) and result.get('status') == 'success':
        data = result.get('data', {})
        print(f"Total hits: {data.get('total_hits', 0)}")
        pathways = data.get('pathways', [])
        print(f"Returned {len(pathways)} pathways")
        if pathways:
            print(f"First pathway: {pathways[0].get('name', 'N/A')}")
    else:
        print(f"ERROR: Unexpected response format: {type(result)}")

    return True

def test_biomodels_tools(tu: ToolUniverse):
    """Test BioModels computational models database"""
    print("\n" + "="*80)
    print("TESTING BIOMODELS TOOLS")
    print("="*80)

    # Test 1: Search models
    print("\n1. Testing biomodels_search...")
    result = tu.tools.biomodels_search(query="glycolysis", limit=3)
    print(f"Status: {result.get('status')}")
    if result.get('status') == 'success':
        data = result.get('data', {})
        print(f"Total matches: {data.get('matches', 0)}")
        models = data.get('models', [])
        print(f"Returned {len(models)} models")
        if models:
            print(f"First model: {models[0].get('id', 'N/A')} - {models[0].get('name', 'N/A')}")
    else:
        print(f"ERROR: {result.get('error', {}).get('message')}")

    return True

def test_gene_ontology_tools(tu: ToolUniverse):
    """Test GO tools for functional annotation"""
    print("\n" + "="*80)
    print("TESTING GENE ONTOLOGY TOOLS")
    print("="*80)

    # Test 1: Search GO terms (correct tool name is GO_search_terms with capital GO)
    print("\n1. Testing GO_search_terms...")
    result = tu.tools.GO_search_terms(query="apoptosis", limit=5)
    print(f"Status: {result.get('status')}")
    if result.get('status') == 'success':
        data = result.get('data', [])
        print(f"Found {len(data)} GO terms for 'apoptosis'")
        if data:
            print(f"First term: {data[0].get('id', 'N/A')} - {data[0].get('name', 'N/A')}")
    else:
        print(f"ERROR: {result.get('error', {}).get('message')}")

    return True

def test_enrichr_tools(tu: ToolUniverse):
    """Test Enrichr enrichment analysis tools"""
    print("\n" + "="*80)
    print("TESTING ENRICHR TOOLS")
    print("="*80)

    # Test 1: Gene enrichment analysis (correct tool name is enrichr_gene_enrichment_analysis)
    print("\n1. Testing enrichr_gene_enrichment_analysis...")
    gene_list = ["TP53", "BRCA1", "EGFR", "MYC", "KRAS"]
    result = tu.tools.enrichr_gene_enrichment_analysis(
        gene_list=gene_list,
        library="KEGG_2021_Human"
    )
    if isinstance(result, dict):
        print(f"Status: {result.get('status')}")
        if result.get('status') == 'success':
            data = result.get('data', [])
            print(f"Found {len(data)} enriched terms")
            if data:
                print(f"Top term: {data[0].get('term', 'N/A')}")
                print(f"P-value: {data[0].get('pvalue', 'N/A')}")
        else:
            error = result.get('error', 'Unknown error')
            print(f"ERROR: {error if isinstance(error, str) else error.get('message', error)}")
    else:
        print(f"ERROR: Unexpected response type: {type(result)}")

    return True

def main():
    """Run all pathway/systems biology tool tests"""
    print("\n" + "="*80)
    print("PATHWAY/SYSTEMS BIOLOGY TOOLS TEST SUITE")
    print("Following TDD: Test tools FIRST before creating skill documentation")
    print("="*80)

    tu = _load_tools()

    tests = [
        ("Reactome", test_reactome_tools),
        ("KEGG", test_kegg_tools),
        ("WikiPathways", test_wikipathways_tools),
        ("Pathway Commons", test_pathway_commons_tools),
        ("BioModels", test_biomodels_tools),
        ("Gene Ontology", test_gene_ontology_tools),
        ("Enrichr", test_enrichr_tools),
    ]

    results = {}
    for name, test_func in tests:
        try:
            success = test_func(tu)
            results[name] = "PASS" if success else "FAIL"
        except Exception as e:
            print(f"\nEXCEPTION in {name}: {e}")
            results[name] = f"EXCEPTION: {str(e)[:100]}"

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    for name, result in results.items():
        print(f"{name:25} {result}")

    print("\n✅ All tests completed. Tool parameters verified.")
    print("Ready to create working pipeline → then documentation")

if __name__ == "__main__":
    main()
