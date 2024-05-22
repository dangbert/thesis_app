import data.alpaca_cleaned_nl.translate_utils as tutils


def test_parse():
    sample1 = {
        "output": "There are several ways technology can be used to improve customer service, including the following:\n\n1. Implementing Chatbots: Chatbots can help provide a faster, more personalized service to your customers. Equipped with artificial intelligence and natural language processing algorithms, chatbots can quickly respond to customer queries, saving customers time and providing them with immediate assistance.\n\n2. Using Social Media: Using social media platforms to interact with customers is an excellent way to improve customer service. By maintaining an active presence on social media, companies can respond to messages and comments promptly, providing customers with an additional, convenient way to reach out for support.\n\n3. Creating a customer-centered website: The company's website should be designed to provide customers with all the relevant information they need about products and services. Features like FAQs and tutorial videos can simplify the user experience and provide better customer service.\n\n4. Collect feedback: Collecting and analyzing feedback can be a powerful tool for improving customer service. By using surveys, feedback forms, and other tools to gather customer feedback, companies can identify areas in which their service needs improvement, and take action to address customer concerns.\n\n5. Personalization: By leveraging customer data, companies can provide a personalized experience to their customers. An AI-powered customer relationship management tool can track customer interactions and provide product\/service recommendations based on their past experiences.\n\nIn summary, technology can be used in various ways to improve customer service. By implementing chatbots, using social media, developing a customer-centered website, collecting feedback, and personalizing the experience, companies can provide better, more efficient service to their customers.",
        "input": "",
        "instruction": "How can you use technology to improve your customer service?",
        "orig_index": 28839,
    }

    sample1_str = """
<===28839===>
<===output===>There are several ways technology can be used to improve customer service, including the following:\n\n1. Implementing Chatbots: Chatbots can help provide a faster, more personalized service to your customers. Equipped with artificial intelligence and natural language processing algorithms, chatbots can quickly respond to customer queries, saving customers time and providing them with immediate assistance.\n\n2. Using Social Media: Using social media platforms to interact with customers is an excellent way to improve customer service. By maintaining an active presence on social media, companies can respond to messages and comments promptly, providing customers with an additional, convenient way to reach out for support.\n\n3. Creating a customer-centered website: The company's website should be designed to provide customers with all the relevant information they need about products and services. Features like FAQs and tutorial videos can simplify the user experience and provide better customer service.\n\n4. Collect feedback: Collecting and analyzing feedback can be a powerful tool for improving customer service. By using surveys, feedback forms, and other tools to gather customer feedback, companies can identify areas in which their service needs improvement, and take action to address customer concerns.\n\n5. Personalization: By leveraging customer data, companies can provide a personalized experience to their customers. An AI-powered customer relationship management tool can track customer interactions and provide product\/service recommendations based on their past experiences.\n\nIn summary, technology can be used in various ways to improve customer service. By implementing chatbots, using social media, developing a customer-centered website, collecting feedback, and personalizing the experience, companies can provide better, more efficient service to their customers.</===output===>
<===input===></===input===>
<===instruction===>How can you use technology to improve your customer service?</===instruction===>
</===28839===>
""".strip()

    output = tutils.serialize(sample1)
    # # write to a.txt and b.txt
    # with open("a.txt", "w") as f:
    #     f.write(output)
    # with open("b.txt", "w") as f:
    #     f.write(sample1_str)

    # breakpoint()
    assert output == sample1_str
    assert tutils.deserialize(sample1_str) == sample1

    sample2 = {
        "output": "She was frustrated and angry after spending over an hour on hold with customer service, only to be transferred multiple times without getting any resolution to her issue.",
        "input": "She was frustrated and angry.",
        "instruction": "Provide a realistic context for the following sentence.",
        "orig_index": 48319,
    }

    sample2_str = """
<===48319===>
<===output===>She was frustrated and angry after spending over an hour on hold with customer service, only to be transferred multiple times without getting any resolution to her issue.</===output===>
<===input===>She was frustrated and angry.</===input===>
<===instruction===>Provide a realistic context for the following sentence.</===instruction===>
</===48319===>
""".strip()

    assert tutils.serialize(sample2) == sample2_str
    assert tutils.deserialize(sample2_str) == sample2
