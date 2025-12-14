
import ragutil.chunks_search
import ragutil.perplexity
import ragutil.scenario_search
import util.chunk
import util.scenario
import util.user



perplexity_client: ragutil.perplexity.PerplexityQuerier = None


def rag_process(user_input: str) -> str:
    # 1. KI-Keyword extraktion

    keywords: list[str] = extract_keywords(perplexity_client, user_input)

    # 2. Szenarien Vektorsuche
    #   Mit den Keywords wird eine Vektorsuche gemacht
    #   Die Top-3 Szenarien werden dabei ausgegeben
    scenarios: list[util.scenario.Scenario] = ragutil.scenario_search.match_keywords(keywords, 3)

    # 3. Chunks Vektorsuche
    for scenario in scenarios:
        questions: list[util.scenario.ScenarioQuestion] = scenario.get_scenario_questions()

        for question in questions:
            chunks: list[util.chunk.DocumentChunk] = ragutil.chunks_search.retrieve_chunks_for_scenario_question(question, 2)
    
    # 4. LLM Aufbereitung
    result = process_final_results(perplexity_client, user_input)


    return result







def extract_keywords(perplexity_client: ragutil.perplexity.PerplexityQuerier, user_input: str) -> list[str]:
    response = perplexity_client.prompt("")

    return response


def process_final_results(perplexity_client: ragutil.perplexity.PerplexityQuerier, user_input: str) -> str:
    response = perplexity_client.prompt("")

    return response


def process_input(user: util.user.User, input: str) -> str:
    return "Placeholder"
