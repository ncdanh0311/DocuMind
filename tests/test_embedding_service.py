import sys
import os

# Thêm thư mục root vào sys.path để import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.services.embedding_service import embedding_service

def test_embeddings():
    print("🚀 Bắt đầu kiểm thử Embedding Service...")
    
    # 1. Định nghĩa chuỗi văn bản mẫu
    texts = [
        "Trường Đại học Công Thương TP.HCM đào tạo đa ngành có thế mạnh về công nghệ thực phẩm.",
        "How is the weather today in Hanoi?"
    ]
    
    # 2. Sinh vector cho tài liệu (passage)
    print("⚙️ Đang sinh vector embedding cho tài liệu (passage)...")
    passage_embeddings = embedding_service.embed_text(texts, is_query=False)
    
    print(f"✅ Đã sinh xong {len(passage_embeddings)} vector.")
    print(f" - Số chiều của Vector 1: {len(passage_embeddings[0])}")
    print(f" - Số chiều của Vector 2: {len(passage_embeddings[1])}")
    
    # Xác minh số chiều vector của multilingual-e5-small phải là 384
    assert len(passage_embeddings[0]) == 384, f"Lỗi: Số chiều vector phải là 384, nhận được {len(passage_embeddings[0])}"
    assert len(passage_embeddings[1]) == 384, f"Lỗi: Số chiều vector phải là 384, nhận được {len(passage_embeddings[1])}"
    
    # 3. Sinh vector cho câu hỏi (query)
    print("⚙️ Đang sinh vector embedding cho câu hỏi (query)...")
    query_text = ["Trụ sở chính của HUIT đặt ở đâu?"]
    query_embeddings = embedding_service.embed_text(query_text, is_query=True)
    
    assert len(query_embeddings[0]) == 384, f"Lỗi: Số chiều vector câu hỏi phải là 384, nhận được {len(query_embeddings[0])}"
    print(f"✅ Sinh vector câu hỏi thành công! Số chiều: {len(query_embeddings[0])}")
    
    # 4. Kiểm tra L2 Normalization (độ dài vector chuẩn hóa L2 phải xấp xỉ bằng 1.0)
    import math
    for idx, vec in enumerate(passage_embeddings + query_embeddings):
        length = math.sqrt(sum(x*x for x in vec))
        print(f" - Độ dài vector #{idx+1} sau chuẩn hóa L2: {length:.6f}")
        assert abs(length - 1.0) < 1e-4, f"Lỗi: Vector chưa được chuẩn hóa L2 chính xác (độ dài = {length})"
        
    print("🎉 Tất cả các kiểm thử cho Embedding Service đã vượt qua xuất sắc!")

if __name__ == "__main__":
    test_embeddings()
