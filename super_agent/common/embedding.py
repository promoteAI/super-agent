from langchain_openai import OpenAIEmbeddings

def get_embeddings():
    """
    获取文本列表的向量表示
    :param texts: List[str]，待编码的文本列表
    :return: List[List[float]]，每个文本的向量
    """
    # 初始化OpenAIEmbeddings，指向远程openai格式的向量模型
    embeddings = OpenAIEmbeddings(
        base_url = "http://10.102.32.39:9999/v1",
        api_key = "gpustack_99bb71d05be3a1e8_cd2464128f60d27dc9a0b48c76f6f0f4",
        model="bge-m3",  # 替换为你的模型名称
        timeout=30
    )
    return embeddings
