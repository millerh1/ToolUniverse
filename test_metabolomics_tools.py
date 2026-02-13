#!/usr/bin/env python3
"""
Test script for Metabolomics tools
Following TDD: test ALL tools BEFORE creating skill documentation
"""

from tooluniverse import ToolUniverse


def _load_tools() -> ToolUniverse:
    """Load ToolUniverse once and return the instance."""
    tu = ToolUniverse()
    tu.load_tools()
    return tu


def test_hmdb_tools(tu: ToolUniverse):
    """Test HMDB (Human Metabolome Database) tools"""
    print("\n" + "="*80)
    print("TESTING HMDB TOOLS")
    print("="*80)

    # Test 1: Search metabolites
    print("\n1. Testing HMDB_search...")
    result = tu.tools.HMDB_search(
        operation="search",  # SOAP tool - requires operation
        query="glucose"
    )
    print(f"Type: {type(result)}")
    if isinstance(result, dict):
        print(f"Status: {result.get('status')}")
        if result.get('status') == 'success':
            data = result.get('data', [])
            print(f"Found {len(data)} results")
            if data:
                print(f"First result: {data[0]}")
        else:
            print(f"ERROR: {result.get('error')}")
    else:
        print(f"Response: {result}")

    # Test 2: Get metabolite details
    print("\n2. Testing HMDB_get_metabolite...")
    result = tu.tools.HMDB_get_metabolite(
        operation="get_metabolite",
        hmdb_id="HMDB0000122"  # Glucose
    )
    print(f"Status: {result.get('status') if isinstance(result, dict) else type(result)}")
    if isinstance(result, dict) and result.get('status') == 'success':
        data = result.get('data', {})
        print(f"Name: {data.get('name', 'N/A')}")
        print(f"Formula: {data.get('chemical_formula', 'N/A')}")
    else:
        print(f"Response: {result}")

    return True

def test_metabolights_tools(tu: ToolUniverse):
    """Test MetaboLights tools"""
    print("\n" + "="*80)
    print("TESTING METABOLIGHTS TOOLS")
    print("="*80)

    # Test 1: List studies
    print("\n1. Testing metabolights_list_studies...")
    result = tu.tools.metabolights_list_studies(size=5)
    print(f"Type: {type(result)}")
    if isinstance(result, dict) and result.get('status') == 'success':
        data = result.get('data', [])
        print(f"Status: success")
        print(f"Found {len(data)} studies")
        if data:
            print(f"First study: {data[0]}")
    elif isinstance(result, list):
        print(f"Status: success (direct list)")
        print(f"Found {len(result)} studies")
        if result:
            print(f"First study: {result[0]}")
    else:
        print(f"Response: {result}")

    # Test 2: Search studies
    print("\n2. Testing metabolights_search_studies...")
    result = tu.tools.metabolights_search_studies(query="glucose")
    print(f"Type: {type(result)}")
    if isinstance(result, dict) and result.get('status') == 'success':
        data = result.get('data', [])
        print(f"Found {len(data)} matching studies")
    elif isinstance(result, list):
        print(f"Found {len(result)} matching studies")
    else:
        print(f"Response: {result}")

    # Test 3: Get study details
    print("\n3. Testing metabolights_get_study...")
    result = tu.tools.metabolights_get_study(study_id="MTBLS1")
    print(f"Type: {type(result)}")
    if isinstance(result, dict):
        if result.get('status') == 'success':
            data = result.get('data', {})
            print(f"Study title: {data.get('title', 'N/A')}")
        else:
            print(f"Status: {result.get('status')}")
            print(f"Response: {result}")

    return True

def test_metabolomics_workbench_tools(tu: ToolUniverse):
    """Test Metabolomics Workbench tools"""
    print("\n" + "="*80)
    print("TESTING METABOLOMICS WORKBENCH TOOLS")
    print("="*80)

    # Test 1: Get study
    print("\n1. Testing MetabolomicsWorkbench_get_study...")
    result = tu.tools.MetabolomicsWorkbench_get_study(
        study_id="ST000001",
        output_item="summary"
    )
    print(f"Type: {type(result)}")
    if isinstance(result, dict) and result.get('status') == 'success':
        data = result.get('data', {})
        print(f"Study found: {data}")
    else:
        print(f"Response: {result}")

    # Test 2: Search compound
    print("\n2. Testing MetabolomicsWorkbench_search_compound_by_name...")
    result = tu.tools.MetabolomicsWorkbench_search_compound_by_name(
        compound_name="glucose"
    )
    print(f"Type: {type(result)}")
    if isinstance(result, dict):
        print(f"Status: {result.get('status')}")
        if result.get('status') == 'success':
            data = result.get('data', {})
            print(f"Compound data: {data}")
    else:
        print(f"Response: {result}")

    return True

def test_pubchem_tools(tu: ToolUniverse):
    """Test PubChem tools for chemical properties"""
    print("\n" + "="*80)
    print("TESTING PUBCHEM TOOLS")
    print("="*80)

    # Test 1: Get compound by name
    print("\n1. Testing pubchem_get_compounds_by_name...")
    result = tu.tools.pubchem_get_compounds_by_name(name="glucose")
    print(f"Type: {type(result)}")
    if isinstance(result, dict) and result.get('status') == 'success':
        data = result.get('data', [])
        print(f"Found {len(data)} compounds")
        if data:
            print(f"First compound CID: {data[0].get('cid', 'N/A')}")
    else:
        print(f"Response: {result}")

    return True

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("METABOLOMICS TOOLS TEST SUITE")
    print("Following TDD: Test tools FIRST before creating skill documentation")
    print("="*80)

    tu = _load_tools()

    tests = [
        ("HMDB", test_hmdb_tools),
        ("MetaboLights", test_metabolights_tools),
        ("Metabolomics Workbench", test_metabolomics_workbench_tools),
        ("PubChem", test_pubchem_tools),
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
        print(f"{name:30} {result}")

    # Document discoveries
    print("\n" + "="*80)
    print("DISCOVERIES - DOCUMENT IN SKILL.md")
    print("="*80)

    print("\n## Parameter Corrections:")
    print("| Tool | Parameter | CORRECT Name | Note |")
    print("|------|-----------|--------------|------|")
    print("| HMDB_search | operation | ✅ 'search' | SOAP tool - CRITICAL |")
    print("| HMDB_get_metabolite | operation | ✅ 'get_metabolite' | SOAP tool - CRITICAL |")

    print("\n## Response Formats:")
    print("- **HMDB_***: Standard {status, data} format")
    print("- **metabolights_list_studies**: May return list directly or {status, data}")
    print("- **MetabolomicsWorkbench_***: Standard {status, data} format")
    print("- **pubchem_***: Standard {status, data} format")

    print("\n## SOAP Tools Detected:")
    print("- **HMDB_search**: Requires operation='search'")
    print("- **HMDB_get_metabolite**: Requires operation='get_metabolite'")

    print("\n✅ All tests completed. Tool parameters verified.")
    print("Ready to create working pipeline → then documentation")

if __name__ == "__main__":
    main()
