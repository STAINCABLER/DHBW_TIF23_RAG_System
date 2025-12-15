import json
import logging
import ragutil.chunks_search
import ragutil.perplexity
import ragutil.scenario_search
import util.chunk
import util.scenario
import util.user



DEBUG: bool = False


perplexity_client: ragutil.perplexity.PerplexityQuerier = ragutil.perplexity.PerplexityQuerier()


def rag_process(user_input: str) -> str:
    logging.info(f"Started RAG Process for `{user_input}`")
    # 1. KI-Keyword extraktion

    keywords: list[str] = extract_keywords(perplexity_client, user_input)
    # keywords = [
    #     "Finanzmanagement",
    #     "Kundenverwaltung",
    #     "Gesundheitswesen"
    # ]
    joined_keywords: str = ",".join(keywords)
    logging.info(f"Retrieved Keywords: `{joined_keywords}`")

    # 2. Szenarien Vektorsuche
    #   Mit den Keywords wird eine Vektorsuche gemacht
    #   Die Top-3 Szenarien werden dabei ausgegeben
   
    scenarios: list[util.scenario.Scenario] = ragutil.scenario_search.match_keywords(keywords, 2)
    names: list[str] = [
        scenario.name
        for scenario in scenarios
    ]
    joined_names: str = ", ".join(names)
    logging.info(f"Mapped Scenarios: `{joined_names}`")

    # 3. Chunks Vektorsuche
    total_blocks: list[str] = []

    for scenario in scenarios:
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

        
        
        
        total_blocks.append(
            "\n\n".join(scenario_blocks)
        )
    logging.info("Retrievd chunks")

    query_part: str = "\n\n".join(total_blocks)
    
    # 4. LLM Aufbereitung
    result = process_final_results(perplexity_client, user_input, query_part)
    logging.info("Returning results")

    return result



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
    response = perplexity_client.prompt(
        f"""
        Folgendes ist ein User Promt, dieser Soll auf ALLE möglichen Stichworte die auf dessen Szenario zutreffen, runtergrebrochen werden.
        MAXIMAL aber 10 Stichworte. In der AUSGABE von DIR, sollen NUR diese Stichworte rauskommen, KEINERLEI ERKLÄRUNG oder sonstiges.
        Diese Stichworte bitte als JSON-Parsable Array. Sonst keinen Text!

        {user_input}
        """
    )

    return json.loads(response)


def process_final_results(perplexity_client: ragutil.perplexity.PerplexityQuerier, user_input: str, query_part: str) -> str:
    response = perplexity_client.prompt(
        f"""
        {user_input}

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


        {query_part}
        """
    )
    #return query_part
    return response


def process_input(user: util.user.User, input: str) -> str:
    return "Placeholder"
