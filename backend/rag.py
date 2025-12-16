import json
import logging
import marko
import time

import ragutil.chunks_search
import ragutil.perplexity
import ragutil.scenario_search
import util.chunk
import util.scenario



DEBUG: bool = False


perplexity_client: ragutil.perplexity.PerplexityQuerier = ragutil.perplexity.PerplexityQuerier()


def rag_process(user_input: str) -> str:
    logging.info(f"Started RAG Process for `{user_input}`")

    start_time_1: float = time.perf_counter()
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

    total_prompt_blocks: list[str] = []
    scenariO_chunk_blocks: list[str] = []

    for scenario in scenarios:
        prompt_block: tuple[str, str] = process_scenario(scenario)
        total_prompt_blocks.append(prompt_block[1])

        res = prompt_block[0]


        scenario_name: str = scenario.name

        desc: str = f"# # {scenario_name}<br>\n# # -{res}"

        scenariO_chunk_blocks.append(desc)

    query_part: str = "\n\n".join(total_prompt_blocks)
    
    start_time_4: float = time.perf_counter()

    # 4. LLM Aufbereitung
    result = process_final_results(perplexity_client, user_input, query_part)
    logging.info("Returning results")

    end_time: float = time.perf_counter()

    delta_perflexity_1: float = start_time_2 - start_time_1
    delta_scenarios: float = start_time_3 - start_time_2
    delta_chunks: float = start_time_4 - start_time_3
    delta_perflexity_2: float = end_time - start_time_4
    rag_delta: float = start_time_4 - start_time_2
    delta: float = end_time - start_time_1

    scenario_info_string = "<br>\n# # <br>\n".join(scenariO_chunk_blocks)

    return result + f"""
    <br>
    <br>
    <hr>
    <br>
    <p>
    # Rag hat {delta:.3f}s benötigt! ({rag_delta:.3f}s ohne AI)<br>
    # - Perplexity 1: {delta_perflexity_1:.3f}s<br>
    # - ScenarioSearch 1: {delta_scenarios:.3f}s<br>
    # - ChunkSearch 1: {delta_chunks:.3f}s<br>
    # - Perplexity 2: {delta_perflexity_2:.3f}s<br>
    <br>
    # Keywords: {keywords}<br>
    <br>
    <br>
    # SzenarioInfo:<br>
    {scenario_info_string}<br>
    <br>
    <hr>
    </p>
    """



def process_scenario(scenario: util.scenario.Scenario) -> tuple[str, str]:
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
    
    chunk_file_names: list[str] = []
    for i in total_chunks:
        file_name: str = i.metadata.source_file
        index: int = i.chunk_index

        chunk_file_names.append(f"{file_name}:{index}")
    
    chunk_file_content: str = ", ".join(chunk_file_names)


    return chunk_file_content, "\n\n".join(scenario_blocks)


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
    
    try:
        response = perplexity_client.prompt(prompt)

        return json.loads(response)
    except:
        return None


def process_final_results(perplexity_client: ragutil.perplexity.PerplexityQuerier, user_input: str, query_part: str) -> str:
    prompt: str = f"""
        DER USER PROMT:
        {user_input}

        VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV
        DEIN SINN DER EXISTENZ:

        Du bist ein DATENBANKEN ENGINEER Experte.
        Deine Aufgabe ist es, eine optimierte Datenbanksystem für ein neues Projekt zu entwerfen.
        Berücksichtige dabei die folgenden Anforderungen:
        - Halte dich an die Anforderungen des User Promts
        - Die Informationen die du über die Kontext Scenarien bekommst sind dein DATENGRUNDLAGEN GOTT. Dies ist deine volle Wissensquelle.
        - Es gibt keinerlei Möglichkeit auf Rückfragen, weshalb du alleine mit den dir gegebenen Informationen arbeiten musst.
        - Evaluiere die besten Technologien und Architekturen, die den Anforderungen am besten entsprechen. NUTZE dein WISSEN aus den SCENARIO KONTEXT. 2 Möglichkeiten MAXIMAL!
        - Erstelle ein detailliertes Datenbankschema, das die Struktur und Beziehungen der Daten klar definiert.
        - Berücksichtige Skalierbarkeit, Leistung und Sicherheit in deinem Design. Solange sie den ANFORDERUNGEN des USER PROMTS entsprechen.
        - Gib eine Begründung für deine Designentscheidungen und die gewählten Technologien.
        DU BEARBEITEST DIE AUFGABE IN DEUTSCHER SPRACHE, ABER ENGLISCHE TECHNISCHE BEGRIFFE SIND ERLAUBT.
        DU ANTWORTEST NUR AUF DEN USER INPUT DES USERS, DER REST IST NUR DEINE WISSENSGRUNDLAGE. NICHTS AUF DAS DU ANTWORTEN SOLLST, ODER DARFST!
        Deine Antwort darf KEINERLEI Links oder Verweise auf externe Quellen enthalten!
        Nutze bitte MARKDOWN Formatierung in deiner Antwort und Volksmundverständliche Sprache mit benötigten Fachbegriffen.
        NIEMALS JavaScript Code oder HTML code in der Antwort nutzen!

        VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV
        DEINE WISSENSDATENBANK:

        {query_part}
        """
    try:
        response = perplexity_client.prompt(prompt)
        return marko.convert(response)
    except:
        return "Perplexity hat nicht geantwortet [Zusammenfassung]"
