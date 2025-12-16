import json
import logging
import time

import ragutil.chunks_search
import ragutil.perplexity
import ragutil.scenario_search
import util.chunk
import util.scenario



DEBUG: bool = False


perplexity_client: ragutil.perplexity.PerplexityQuerier = ragutil.perplexity.PerplexityQuerier()


def rag_process(user_input: str) -> tuple[float, float, float]:
    logging.info(f"Started RAG Process for `{user_input}`")

    # 1. KI-Keyword extraktion
    keywords: list[str] = extract_keywords(perplexity_client, user_input)

    if not keywords:
        return "Perplexity hat nicht geantworte [Keywords]"
    start_time_2: float = time.perf_counter()

    joined_keywords: str = ",".join(keywords)
    logging.info(f"Retrieved Keywords: `{joined_keywords}`")


    # 2. Szenarien Vektorsuche
    scenarios: list[util.scenario.Scenario] = ragutil.scenario_search.match_keywords(keywords, 2)
    names: list[str] = [
        scenario.name
        for scenario in scenarios
    ]
    joined_names: str = ", ".join(names)
    logging.info(f"Mapped Scenarios: `{joined_names}`")

    start_time_3: float = time.perf_counter()
    # 3. Chunks Vektorsuche
    logging.info("Retrieved chunks")

    scenario_chunks: list[str] = []

    for scenario in scenarios:
        prompt_block: str = process_scenario(scenario)
        scenario_chunks.append(prompt_block)
    
    start_time_4: float = time.perf_counter()

    logging.info("Returning results")


    delta_scenarios: float = start_time_3 - start_time_2
    delta_chunks: float = start_time_4 - start_time_3
    rag_delta: float = start_time_4 - start_time_2


    return tuple([delta_scenarios, delta_chunks, rag_delta])



def process_scenario(scenario: util.scenario.Scenario) -> str:
    total_chunks: list[util.chunk.DocumentChunk] = []
    questions: list[util.scenario.ScenarioQuestion] = scenario.get_scenario_questions()

    scenario_blocks: list[str] = []

    scenario_blocks.append(scenario.description)

    if DEBUG:
        print(scenario.name)

    for question in questions:
        chunks: list[util.chunk.DocumentChunk] = ragutil.chunks_search.retrieve_chunks_for_scenario_question(question, 2)

        reduced_chunks: list[util.chunk.DocumentChunk] = [
            i
            for i in chunks
            if i not in total_chunks
        ]

        

        for i in reduced_chunks:
            total_chunks.append(i)
        
        if DEBUG:
            print("\t- " + question.question)
            print("\t   " + question.answer)
            r = [
                chunk.metadata.source_file
                for chunk in reduced_chunks
            ]
            print("\t\t" + " ".join(r))
            print("")

        question_block: str = build_question_block(question, reduced_chunks)
        scenario_blocks.append(question_block)
    
    names: list[str] = [
        i.metadata.source_file
        for i in total_chunks
    ]
    chunk_names: str = ", ".join(names)
    
    return chunk_names


def build_question_block(question: util.scenario.ScenarioQuestion, chunks: list[util.chunk.DocumentChunk]) -> str:
    """
    <Frage>:\n
    <ChunkTitel>: <ChunkText>\n
    <ChunktTitel2>: <ChunkText2>\n
    
    """
    blocks: list[str] = []

    blocks.append(question.question)

    for chunk in chunks:
        chunk_text: str = chunk.chunk_text
        header_name: str = chunk.metadata.heading

        chunk_block: str = f"{header_name}: {chunk_text}"

        blocks.append(chunk_block)

    return "\n".join(blocks)




def extract_keywords(perplexity_client: ragutil.perplexity.PerplexityQuerier, user_input: str) -> list[str]:
    prompt: str = f"""
        Folgendes ist ein User Promt, dieser Soll auf ALLE möglichen Stichworte die auf dessen Szenario zutreffen, runtergrebrochen werden.
        MAXIMAL aber 10 Stichworte. In der AUSGABE von DIR, sollen NUR diese Stichworte rauskommen, KEINERLEI ERKLÄRUNG oder sonstiges.
        Diese Stichworte bitte als JSON-Parsable Array. Sonst keinen Text!

        {user_input}
        """
    
    return [
        "Backrezepte",
        "Datenbank",
        "Verwaltung",
        "Anleitung",
        "Zutaten",
        "Rezeptdatenbank",
        "Nährwerte",
        "Zubereitung",
        "Rezeptsoftware",
        "Bäckerei"
    ]


