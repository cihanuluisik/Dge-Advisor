import os, sys, pytest

os.environ['IS_TESTING'] = '1'
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from retriever.retriever import Retriever

class TestRetriever:
    
    def test_retriever_initialization(self):
        retriever = Retriever()
        assert retriever is not None
        assert hasattr(retriever, 'query_engine')
        assert retriever.query_engine is not None
    
    def test_procurement_procedures_query(self):
        retriever = Retriever()
        result = retriever.search("What is the notice period for termination of employment?")
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0
        # Accept current formatted output
        assert ("Document:" in result and "Page:" in result) or ("File Path:" in result)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])