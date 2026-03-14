
    """Document Processor - 文档处理"""
    import re
    from typing import List, Dict, Optional, Any, Callable
    from pathlib import Path
    import json
    
    class DocumentChunk:
        """文档块"""
        def __init__(self, text: str, start_idx: int, end_idx: int, metadata: Dict = None):
            self.text = text
            self.start_idx = start_idx
            self.end_idx = end_idx
            self.metadata = metadata or {}
            
        def __repr__(self):
            return f"DocumentChunk({len(text)} chars, idx={start_idx}-{end_idx})"
            
    class DocumentProcessor:
        """文档处理器"""
        
        def __init__(self, chunk_size: int = 500, overlap: int = 50):
            self.chunk_size = chunk_size
            self.overlap = overlap
            
        def process(self, text: str, metadata: Optional[Dict] = None) -> List[DocumentChunk]:
            """处理文档"""
            chunks = []
            
            # 按句子分割
            sentences = self._split_sentences(text)
            
            current_chunk = ""
            current_start = 0
            current_length = 0
            
            for i, sent in enumerate(sentences):
                sent_len = len(sent)
                
                if current_length + sent_len <= self.chunk_size:
                    current_chunk += sent + " "
                    current_length += sent_len + 1
                else:
                    # 保存当前块
                    if current_chunk:
                        chunks.append(DocumentChunk(
                            text=current_chunk.strip(),
                            start_idx=current_start,
                            end_idx=current_start + current_length,
                            metadata=metadata
                        ))
                        
                    # 开始新块(有重叠)
                    if self.overlap > 0 and chunks:
                        # 取上一个块的后overlap个字符
                        prev = chunks[-1].text
                        overlap_start = max(0, len(prev) - self.overlap)
                        current_chunk = prev[overlap_start:] + sent + " "
                        current_start = chunks[-1].start_idx + overlap_start
                        current_length = len(current_chunk)
                    else:
                        current_chunk = sent + " "
                        current_start += current_length
                        current_length = sent_len + 1
                        
            # 最后一个块
            if current_chunk.strip():
                chunks.append(DocumentChunk(
                    text=current_chunk.strip(),
                    start_idx=current_start,
                    end_idx=current_start + current_length,
                    metadata=metadata
                ))
                
            return chunks
            
        def _split_sentences(self, text: str) -> List[str]:
            """分割句子"""
            # 简单按标点分割
            sentences = re.split(r'[。！？；\n]+', text)
            return [s.strip() for s in sentences if s.strip()]
            
    class PDFProcessor(DocumentProcessor):
        """PDF处理器"""
        
        def extract_text(self, pdf_path: Path) -> str:
            """提取PDF文本"""
            try:
                import PyPDF2
                
                text = ""
                with open(pdf_path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                        
                return text
            except Exception as e:
                print(f"PDF extraction error: {e}")
                return ""
                
        def process_pdf(self, pdf_path: Path, metadata: Optional[Dict] = None) -> List[DocumentChunk]:
            """处理PDF"""
            text = self.extract_text(pdf_path)
            return self.process(text, metadata)
            
    class MarkdownProcessor(DocumentProcessor):
        """Markdown处理器"""
        
        def process_markdown(self, md_text: str, metadata: Optional[Dict] = None) -> List[DocumentChunk]:
            """处理Markdown"""
            # 提取标题
            headings = re.findall(r'^#+\s+(.+)$', md_text, re.MULTILINE)
            
            # 移除markdown语法
            text = md_text
            text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # 链接
            text = re.sub(r'[*_]+([*_]+)', r'\1', text)  # 加粗斜体
            text = re.sub(r'`{3}[\s\S]*?`{3}', '', text)  # 代码块
            text = re.sub(r'`[^`]+`', '', text)  # 行内代码
            
            return self.process(text, {**(metadata or {}), "headings": headings})
            
    class WebProcessor(DocumentProcessor):
        """网页处理器"""
        
        def extract_from_html(self, html: str) -> str:
            """从HTML提取文本"""
            # 移除脚本和样式
            text = re.sub(r'<script[\s\S]*?</script>', '', html, flags=re.IGNORECASE)
            text = re.sub(r'<style[\s\S]*?</style>', '', text, flags=re.IGNORECASE)
            
            # 替换标签为换行
            text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
            text = re.sub(r'</p>', '\n\n', text, flags=re.IGNORECASE)
            text = re.sub(r'</div>', '\n', text, flags=re.IGNORECASE)
            text = re.sub(r'</h[1-6]>', '\n\n', text, flags=re.IGNORECASE)
            
            # 移除所有标签
            text = re.sub(r'<[^>]+>', '', text)
            
            # 解码HTML实体
            text = text.replace('&nbsp;', ' ')
            text = text.replace('&lt;', '<')
            text = text.replace('&gt;', '>')
            text = text.replace('&amp;', '&')
            
            return text
            
        def process_url(self, url: str) -> List[DocumentChunk]:
            """处理URL"""
            import requests
            
            try:
                resp = requests.get(url, timeout=10)
                html = resp.text
                text = self.extract_from_html(html)
                
                return self.process(text, {"source_url": url})
            except Exception as e:
                print(f"URL processing error: {e}")
                return []
