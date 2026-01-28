"""
存储管理 - 历史记录的保存和查询
"""
import csv
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class Storage:
    """历史记录存储管理"""
    
    def __init__(self, history_file: str = "data/history.json"):
        self.history_file = Path(history_file)
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """确保历史文件存在"""
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.history_file.exists():
            self._save_data({
                "records": [],
                "statistics": {
                    "total_count": 0,
                    "by_type": {},
                    "last_updated": None
                }
            })
    
    def _load_data(self) -> dict:
        """加载历史数据"""
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"records": [], "statistics": {"total_count": 0, "by_type": {}, "last_updated": None}}
    
    def _save_data(self, data: dict):
        """保存历史数据"""
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def save_record(
        self,
        question: str,
        question_type: str,
        yao_sequence: List[int],
        ben_gua: str,
        bian_gua: Optional[str],
        changing_lines: List[int],
        interpretation: str
    ) -> str:
        """
        保存一条算命记录
        返回记录ID
        """
        data = self._load_data()
        
        record_id = str(uuid.uuid4())[:8]
        record = {
            "id": record_id,
            "created_at": datetime.now().isoformat(),
            "question": question,
            "question_type": question_type,
            "yao_sequence": yao_sequence,
            "ben_gua": ben_gua,
            "bian_gua": bian_gua,
            "changing_lines": changing_lines,
            "interpretation": interpretation
        }
        
        data["records"].insert(0, record)  # 新记录放在最前面
        
        # 更新统计
        data["statistics"]["total_count"] += 1
        data["statistics"]["by_type"][question_type] = data["statistics"]["by_type"].get(question_type, 0) + 1
        data["statistics"]["last_updated"] = datetime.now().isoformat()
        
        # 限制最大记录数
        max_records = 1000
        if len(data["records"]) > max_records:
            data["records"] = data["records"][:max_records]
        
        self._save_data(data)
        return record_id
    
    def get_history(self, limit: int = 10, question_type: Optional[str] = None) -> List[dict]:
        """
        获取历史记录
        """
        data = self._load_data()
        records = data["records"]
        
        if question_type:
            records = [r for r in records if r["question_type"] == question_type]
        
        return records[:limit]
    
    def get_record_by_id(self, record_id: str) -> Optional[dict]:
        """根据ID获取单条记录"""
        data = self._load_data()
        for record in data["records"]:
            if record["id"] == record_id:
                return record
        return None
    
    def save_followup(self, record_id: str, question: str, answer: str) -> bool:
        """
        保存追问记录到对应的主记录中
        """
        data = self._load_data()
        
        for record in data["records"]:
            if record["id"] == record_id:
                # 初始化追问列表
                if "followups" not in record:
                    record["followups"] = []
                
                # 添加追问记录
                record["followups"].append({
                    "timestamp": datetime.now().isoformat(),
                    "question": question,
                    "answer": answer
                })
                
                self._save_data(data)
                return True
        
        return False
    
    def get_followups(self, record_id: str) -> List[dict]:
        """获取某条记录的所有追问"""
        record = self.get_record_by_id(record_id)
        if record:
            return record.get("followups", [])
        return []
    
    def get_statistics(self) -> dict:
        """获取统计信息"""
        data = self._load_data()
        return data["statistics"]
    
    def clear_history(self):
        """清空历史记录"""
        self._save_data({
            "records": [],
            "statistics": {
                "total_count": 0,
                "by_type": {},
                "last_updated": None
            }
        })
    
    def export_to_json(self, output_path: str = None) -> str:
        """
        导出历史记录为JSON文件
        返回导出文件路径
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"data/export_history_{timestamp}.json"
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = self._load_data()
        
        # 创建导出数据
        export_data = {
            "export_time": datetime.now().isoformat(),
            "total_records": len(data["records"]),
            "statistics": data["statistics"],
            "records": data["records"]
        }
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        return str(output_file)
    
    def export_to_csv(self, output_path: str = None) -> str:
        """
        导出历史记录为CSV文件
        返回导出文件路径
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"data/export_history_{timestamp}.csv"
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = self._load_data()
        records = data["records"]
        
        # CSV表头
        fieldnames = [
            "id", "created_at", "question", "question_type",
            "ben_gua", "bian_gua", "changing_lines", "yao_sequence",
            "interpretation", "followup_count"
        ]
        
        with open(output_file, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for record in records:
                row = {
                    "id": record.get("id", ""),
                    "created_at": record.get("created_at", ""),
                    "question": record.get("question", ""),
                    "question_type": record.get("question_type", ""),
                    "ben_gua": record.get("ben_gua", ""),
                    "bian_gua": record.get("bian_gua", "") or "",
                    "changing_lines": ",".join(str(x) for x in record.get("changing_lines", [])),
                    "yao_sequence": ",".join(str(x) for x in record.get("yao_sequence", [])),
                    "interpretation": record.get("interpretation", "").replace("\n", " | "),
                    "followup_count": len(record.get("followups", []))
                }
                writer.writerow(row)
        
        return str(output_file)
    
    def import_from_json(self, input_path: str) -> int:
        """
        从JSON文件导入历史记录
        返回导入的记录数
        """
        input_file = Path(input_path)
        if not input_file.exists():
            raise FileNotFoundError(f"文件不存在: {input_path}")
        
        with open(input_file, "r", encoding="utf-8") as f:
            import_data = json.load(f)
        
        # 兼容两种格式：导出格式和原始数据格式
        if "records" in import_data:
            new_records = import_data["records"]
        else:
            new_records = import_data
        
        if not isinstance(new_records, list):
            raise ValueError("无效的导入数据格式")
        
        # 加载现有数据
        data = self._load_data()
        existing_ids = {r["id"] for r in data["records"]}
        
        # 合并记录，跳过已存在的ID
        imported_count = 0
        for record in new_records:
            if record.get("id") and record["id"] not in existing_ids:
                data["records"].append(record)
                existing_ids.add(record["id"])
                imported_count += 1
                
                # 更新统计
                q_type = record.get("question_type", "其他")
                data["statistics"]["total_count"] += 1
                data["statistics"]["by_type"][q_type] = data["statistics"]["by_type"].get(q_type, 0) + 1
        
        data["statistics"]["last_updated"] = datetime.now().isoformat()
        
        # 按时间排序
        data["records"].sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        self._save_data(data)
        return imported_count


if __name__ == "__main__":
    # 测试
    storage = Storage()
    
    # 保存测试记录
    rid = storage.save_record(
        question="测试问题",
        question_type="事业",
        yao_sequence=[7, 8, 6, 9, 7, 8],
        ben_gua="天水讼",
        bian_gua="天火同人",
        changing_lines=[3, 4],
        interpretation="测试解读内容"
    )
    print(f"保存成功，ID: {rid}")
    
    # 查询
    history = storage.get_history(limit=5)
    print(f"历史记录: {len(history)} 条")
    
    stats = storage.get_statistics()
    print(f"统计: {stats}")
