"""
使用示例: 演示词向量 → 句向量 → 上下文嵌入的完整演进过程。
包含三种向量化方法的对比演示。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from word_embedding import OneHotEncoder, TFIDFEncoder
from sentence_embedding import (
    SimpleWordVectors,
    BagOfWordsAverage,
    TFIDFWeightedAverage,
    SimpleAttentionSentence,
)
from contextual_embedding import (
    BiContextualEncoder,
    SelfAttentionLayer,
    TransformerEncoderLayer,
)


def demo_word_embedding():
    """演示词向量化方法"""
    print("=" * 60)
    print("  词向量化 — Word Embedding 演示")
    print("=" * 60)

    # 示例语料库
    corpus = [
        ["我", "喜欢", "猫"],
        ["我", "喜欢", "狗"],
        ["猫", "和", "狗", "都是", "宠物"],
        ["我", "养", "了", "一只", "猫"],
    ]

    # ---------- 独热编码 ----------
    print("\n1. 独热编码 (One-Hot Encoding):")
    onehot = OneHotEncoder()
    onehot.build_vocab(corpus)
    print(f"   词汇表大小: {onehot.vocab_size}")
    print(f"   词汇表: {onehot.vocab}")

    # 编码示例词
    for word in ["猫", "狗", "宠物", "未知词"]:
        vec = onehot.encode(word)
        if vec:
            # 只显示前 5 维
            print(f"   '{word}' → [{', '.join(map(str, vec[:5]))}, ...] "
                  f"(维度: {len(vec)})")
        else:
            print(f"   '{word}' → None (不在词汇表中)")

    # ---------- TF-IDF ----------
    print("\n2. TF-IDF 编码:")
    tfidf_enc = TFIDFEncoder()
    tfidf_enc.build_vocab(corpus)

    test_doc = ["我", "喜欢", "猫"]
    vector = tfidf_enc.transform(test_doc)
    print(f"   文档: {test_doc}")
    print(f"   向量维度: {len(vector)}")

    # 获取关键词
    top_words = tfidf_enc.get_top_words(test_doc, top_k=3)
    print(f"   Top 3 关键词:")
    for word, score in top_words:
        print(f"     {word}: {score:.4f}")


def demo_sentence_embedding():
    """演示句向量化方法"""
    print("\n" + "=" * 60)
    print("  句向量化 — Sentence Embedding 演示")
    print("=" * 60)

    # 创建基础词向量
    word_vecs = SimpleWordVectors(dim=8)

    # 示例句子
    sentences = [
        ["我", "喜欢", "猫"],
        ["我", "喜欢", "狗"],
        ["猫", "和", "狗", "是", "宠物"],
    ]

    # ---------- 词袋平均 ----------
    print("\n1. 词袋平均 (Bag-of-Words Average):")
    bow = BagOfWordsAverage(word_vecs)
    for sent in sentences:
        vec = bow.encode(sent)
        if vec:
            print(f"   {sent} → [{', '.join(f'{v:.3f}' for v in vec[:3])}, ...]")

    # ---------- TF-IDF 加权 ----------
    print("\n2. TF-IDF 加权平均:")
    # 预计算 IDF
    corpus = [
        ["我", "喜欢", "猫"],
        ["我", "喜欢", "狗"],
        ["猫", "和", "狗", "是", "宠物"],
    ]
    from collections import Counter
    num_docs = len(corpus)
    doc_freq = Counter()
    for doc in corpus:
        for word in set(doc):
            doc_freq[word] += 1
    idf = {w: __import__("math").log(num_docs / df) + 1 for w, df in doc_freq.items()}

    tfidf_avg = TFIDFWeightedAverage(word_vecs, idf)
    for sent in sentences:
        vec = tfidf_avg.encode(sent)
        if vec:
            print(f"   {sent} → [{', '.join(f'{v:.3f}' for v in vec[:3])}, ...]")

    # ---------- 注意力加权 ----------
    print("\n3. 简单注意力加权:")
    attn_sent = SimpleAttentionSentence(word_vecs, dim=8)
    for sent in sentences:
        vec = attn_sent.encode(sent)
        if vec:
            print(f"   {sent} → [{', '.join(f'{v:.3f}' for v in vec[:3])}, ...]")
        # 显示注意力权重
        weights = attn_sent.get_attention_weights(sent)
        if weights:
            weight_str = ", ".join(f"{w}={a:.2f}" for w, a in weights)
            print(f"     注意力: {weight_str}")


def demo_contextual_embedding():
    """演示上下文感知嵌入"""
    print("\n" + "=" * 60)
    print("  上下文感知嵌入 — Contextual Embedding 演示")
    print("=" * 60)

    word_vecs = SimpleWordVectors(dim=8)

    # 包含歧义词的句子
    test_sentences = [
        ["银行", "在", "河边"],         # 银行 = 河岸
        ["我", "去", "银行", "取钱"],  # 银行 = 金融机构
        ["苹果", "很", "好吃"],        # 苹果 = 水果
        ["苹果", "发布", "新", "手机"],  # 苹果 = 公司
    ]

    # ---------- 双向上下文 ----------
    print("\n1. 双向上下文编码器:")
    bi_encoder = BiContextualEncoder(word_vecs, context_weight=0.1)
    for sent in test_sentences:
        contextual_vecs = bi_encoder.encode_sentence(sent)
        # 找到"银行"或"苹果"的向量
        for i, word in enumerate(sent):
            if word in ("银行", "苹果") and contextual_vecs[i]:
                vec = contextual_vecs[i]
                print(f"   '{word}' in {sent}")
                print(f"     向量: [{', '.join(f'{v:.3f}' for v in vec[:4])}, ...]")

    # ---------- 自注意力 ----------
    print("\n2. 自注意力层:")
    attn_layer = SelfAttentionLayer(dim=8)
    for sent in test_sentences[:2]:
        # 获取基础向量
        base_vecs = []
        valid_words = []
        for word in sent:
            vec = word_vecs.get_vector(word)
            if vec:
                base_vecs.append(vec)
                valid_words.append(word)

        if base_vecs:
            output = attn_layer.forward(base_vecs)
            print(f"   句子: {valid_words}")
            print(f"   输出: [{', '.join(f'{v:.3f}' for v in output[0][:3])}, ...]")

    # ---------- Transformer Encoder ----------
    print("\n3. Transformer Encoder 层:")
    encoder = TransformerEncoderLayer(dim=8)
    for sent in test_sentences[:1]:
        base_vecs = []
        valid_words = []
        for word in sent:
            vec = word_vecs.get_vector(word)
            if vec:
                base_vecs.append(vec)
                valid_words.append(word)

        if base_vecs:
            output = encoder.forward(base_vecs)
            print(f"   输入: {valid_words}")
            print(f"   编码后: [{', '.join(f'{v:.3f}' for v in output[0][:3])}, ...]")


def demo_embedding_comparison():
    """对比不同向量化方法"""
    print("\n" + "=" * 60)
    print("  向量化方法对比")
    print("=" * 60)

    # 测试句子
    sent = ["我", "喜欢", "在", "河边", "的", "银行", "散步"]

    print(f"\n句子: {sent}")
    print("\n各方法输出:")

    # 词向量
    word_vecs = SimpleWordVectors(dim=8)
    bow = BagOfWordsAverage(word_vecs)
    vec_bow = bow.encode(sent)
    if vec_bow:
        print(f"  词袋平均: [{', '.join(f'{v:.3f}' for v in vec_bow[:3])}, ...]")

    # 注意力
    attn = SimpleAttentionSentence(word_vecs, dim=8)
    vec_attn = attn.encode(sent)
    if vec_attn:
        print(f"  注意力:   [{', '.join(f'{v:.3f}' for v in vec_attn[:3])}, ...]")

    # 上下文
    bi = BiContextualEncoder(word_vecs, context_weight=0.1)
    vec_bi = bi.encode_sentence(sent)
    if vec_bi and vec_bi[0]:
        print(f"  双向上下文: [{', '.join(f'{v:.3f}' for v in vec_bi[0][:3])}, ...]")

    # Transformer
    base_vecs = [word_vecs.get_vector(w) for w in sent]
    base_vecs = [v for v in base_vecs if v]
    if base_vecs:
        transformer = TransformerEncoderLayer(dim=8)
        vec_trans = transformer.forward(base_vecs)
        if vec_trans:
            print(f"  Transformer: [{', '.join(f'{v:.3f}' for v in vec_trans[0][:3])}, ...]")


if __name__ == "__main__":
    demo_word_embedding()
    demo_sentence_embedding()
    demo_contextual_embedding()
    demo_embedding_comparison()
