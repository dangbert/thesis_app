import os
import data.alpaca_cleaned_nl.translate_utils as tutils
import data.alpaca_cleaned_nl.manage as manage

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

SAMPLE_DATASET_PATH = os.path.join(SCRIPT_DIR, "sample_dataset.jsonl")
SAMPLE_DEEPL_PATH = os.path.join(SCRIPT_DIR, "sample_deepl.txt")
# SAMPLE_DATASET_PATH = manage.TRANSLATED_PATH

SAMPLE1 = {
    "output": "There are several ways technology can be used to improve customer service, including the following:\n\n1. Implementing Chatbots: Chatbots can help provide a faster, more personalized service to your customers. Equipped with artificial intelligence and natural language processing algorithms, chatbots can quickly respond to customer queries, saving customers time and providing them with immediate assistance.\n\n2. Using Social Media: Using social media platforms to interact with customers is an excellent way to improve customer service. By maintaining an active presence on social media, companies can respond to messages and comments promptly, providing customers with an additional, convenient way to reach out for support.\n\n3. Creating a customer-centered website: The company's website should be designed to provide customers with all the relevant information they need about products and services. Features like FAQs and tutorial videos can simplify the user experience and provide better customer service.\n\n4. Collect feedback: Collecting and analyzing feedback can be a powerful tool for improving customer service. By using surveys, feedback forms, and other tools to gather customer feedback, companies can identify areas in which their service needs improvement, and take action to address customer concerns.\n\n5. Personalization: By leveraging customer data, companies can provide a personalized experience to their customers. An AI-powered customer relationship management tool can track customer interactions and provide product\/service recommendations based on their past experiences.\n\nIn summary, technology can be used in various ways to improve customer service. By implementing chatbots, using social media, developing a customer-centered website, collecting feedback, and personalizing the experience, companies can provide better, more efficient service to their customers.",
    "input": "",
    "instruction": "How can you use technology to improve your customer service?",
    "orig_index": 28839,
}

SAMPLE1_STR = """
<===@28839===>
<===0===></===0===>
<===1===>How can you use technology to improve your customer service?</===1===>
<===2===>There are several ways technology can be used to improve customer service, including the following:\n\n1. Implementing Chatbots: Chatbots can help provide a faster, more personalized service to your customers. Equipped with artificial intelligence and natural language processing algorithms, chatbots can quickly respond to customer queries, saving customers time and providing them with immediate assistance.\n\n2. Using Social Media: Using social media platforms to interact with customers is an excellent way to improve customer service. By maintaining an active presence on social media, companies can respond to messages and comments promptly, providing customers with an additional, convenient way to reach out for support.\n\n3. Creating a customer-centered website: The company's website should be designed to provide customers with all the relevant information they need about products and services. Features like FAQs and tutorial videos can simplify the user experience and provide better customer service.\n\n4. Collect feedback: Collecting and analyzing feedback can be a powerful tool for improving customer service. By using surveys, feedback forms, and other tools to gather customer feedback, companies can identify areas in which their service needs improvement, and take action to address customer concerns.\n\n5. Personalization: By leveraging customer data, companies can provide a personalized experience to their customers. An AI-powered customer relationship management tool can track customer interactions and provide product\/service recommendations based on their past experiences.\n\nIn summary, technology can be used in various ways to improve customer service. By implementing chatbots, using social media, developing a customer-centered website, collecting feedback, and personalizing the experience, companies can provide better, more efficient service to their customers.</===2===>
</===@28839===>
""".strip()

SAMPLE2 = {
    "output": "She was frustrated and angry after spending over an hour on hold with customer service, only to be transferred multiple times without getting any resolution to her issue.",
    "input": "She was frustrated and angry.",
    "instruction": "Provide a realistic context for the following sentence.",
    "orig_index": 48319,
}

SAMPLE2_STR = """
<===@48319===>
<===0===>She was frustrated and angry.</===0===>
<===1===>Provide a realistic context for the following sentence.</===1===>
<===2===>She was frustrated and angry after spending over an hour on hold with customer service, only to be transferred multiple times without getting any resolution to her issue.</===2===>
</===@48319===>
""".strip()

SAMPLE2_DUTCH_STR = """
<===@48319===>
<===0===>Ze was gefrustreerd en boos.</===0===>
<===1===>Bedenk een realistische context voor de volgende zin.</===1===>
<===2===>Ze was gefrustreerd en boos nadat ze meer dan een uur in de wacht had gestaan bij de klantenservice, alleen maar om meerdere keren te worden doorverbonden zonder enige oplossing te krijgen voor haar probleem.</===2===>
</===@48319===>
""".strip()

SAMPLE2_DUCTH = {
    "output": "Ze was gefrustreerd en boos nadat ze meer dan een uur in de wacht had gestaan bij de klantenservice, alleen maar om meerdere keren te worden doorverbonden zonder enige oplossing te krijgen voor haar probleem.",
    "input": "Ze was gefrustreerd en boos.",
    "instruction": "Bedenk een realistische context voor de volgende zin.",
    "orig_index": 48319,
}


def test_serialize_sample():
    assert tutils.serialize_sample(SAMPLE1) == SAMPLE1_STR
    assert tutils.serialize_sample(SAMPLE2) == SAMPLE2_STR
    assert tutils.serialize_sample(SAMPLE2_DUCTH) == SAMPLE2_DUTCH_STR


def test_deserialize_sample():
    assert tutils.deserialize_sample(SAMPLE1_STR) == SAMPLE1
    assert tutils.deserialize_sample(SAMPLE2_STR) == SAMPLE2
    assert tutils.deserialize_sample(SAMPLE2_DUTCH_STR) == SAMPLE2_DUCTH


def test_integration(tmpdir):
    dataset, dataset_dict = manage.load_local_dataset(SAMPLE_DATASET_PATH)

    for i, item in enumerate(dataset):
        assert isinstance(item, dict)
        cereal = tutils.serialize_sample(item)
        assert tutils.deserialize_sample(cereal) == item

    for ext in ["txt", "docx"]:
        fname = os.path.join(tmpdir, f"out.{ext}")
        tutils.serialize_dataset(dataset, fname, assert_sanity=True)

        new_dataset = tutils.deserialize_dataset(fname)
        assert len(new_dataset) == len(dataset)
        for i in range(len(new_dataset)):
            assert new_dataset[i] == dataset[i]
    # test robustness to varying number of equals signs
    dataset = tutils.deserialize_dataset(SAMPLE_DEEPL_PATH)
    assert len(dataset) == 6
