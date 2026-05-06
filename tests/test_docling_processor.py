import sys
import os

# Thêm thư mục root vào sys.path để có thể import được backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.processor.document_processor import DocumentProcessor

def test_docling():
    # Đường dẫn tới file PDF mẫu
    sample_pdf = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ANFIS.docx"))
    
    if not os.path.exists(sample_pdf):
        print(f"❌ Không tìm thấy file mẫu tại: {sample_pdf}")
        return

    print(f"🔍 Đang bắt đầu xử lý file: {os.path.basename(sample_pdf)} bằng Docling...")
    
    try:
        # Khởi tạo processor
        processor = DocumentProcessor(chunk_size=800, chunk_overlap=100)
        
        # Xử lý tài liệu
        chunks = processor.process_document(sample_pdf)
        
        print(f"✅ Xử lý thành công! Tổng số mảnh (chunks) tạo ra: {len(chunks)}")
        print("\n" + "="*50)
        print("BẢN TIN CHI TIẾT 3 MẢNH ĐẦU TIÊN:")
        print("="*50)
        
        for i, chunk in enumerate(chunks[:3]):
            print(f"\n--- Mảnh #{i+1} ---")
            print(f"Nguồn: {chunk['metadata']['source']}")
            print(f"Nội dung (định dạng Markdown):")
            print("-" * 20)
            print(chunk['content'])
            print("-" * 20)
            
        print("\n" + "="*50)
        print("Thử nghiệm hoàn tất!")
        
    except Exception as e:
        print(f"❌ Có lỗi xảy ra trong quá trình xử lý: {str(e)}")

if __name__ == "__main__":
    test_docling()
