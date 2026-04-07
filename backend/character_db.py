"""
角色数据库模块
管理角色档案的存储、检索和分组
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import asdict
from datetime import datetime
import uuid

from character_analyzer import CharacterProfile


class CharacterDatabase:
    """角色数据库"""
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = Path(__file__).parent / "data" / "characters"
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 角色库文件
        self.characters_file = self.data_dir / "characters.json"
        # 角色组文件
        self.groups_file = self.data_dir / "groups.json"
        # 书库文件
        self.books_file = self.data_dir / "books.json"
        
        self._init_files()
    
    def _init_files(self):
        """初始化数据文件"""
        if not self.characters_file.exists():
            self._save_json(self.characters_file, {})
        if not self.groups_file.exists():
            self._save_json(self.groups_file, {})
        if not self.books_file.exists():
            self._save_json(self.books_file, {})
    
    def _load_json(self, filepath: Path) -> Dict:
        """加载JSON文件"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_json(self, filepath: Path, data: Dict):
        """保存JSON文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    # ==================== 角色管理 ====================
    
    def add_character(self, character: CharacterProfile) -> CharacterProfile:
        """添加角色到数据库"""
        data = self._load_json(self.characters_file)
        data[character.id] = character.to_dict()
        self._save_json(self.characters_file, data)
        return character
    
    def get_character(self, character_id: str) -> Optional[CharacterProfile]:
        """获取单个角色"""
        data = self._load_json(self.characters_file)
        if character_id in data:
            return CharacterProfile.from_dict(data[character_id])
        return None
    
    def get_all_characters(self) -> List[CharacterProfile]:
        """获取所有角色"""
        data = self._load_json(self.characters_file)
        return [CharacterProfile.from_dict(c) for c in data.values()]
    
    def get_characters_by_book(self, book_id: str) -> List[CharacterProfile]:
        """获取指定书籍的所有角色"""
        all_chars = self.get_all_characters()
        return [c for c in all_chars if c.book_title == book_id or c.id.startswith(book_id)]
    
    def get_characters_by_tags(self, tags: List[str]) -> List[CharacterProfile]:
        """获取带有指定标签的角色"""
        all_chars = self.get_all_characters()
        return [c for c in all_chars if any(tag in c.tags for tag in tags)]
    
    def update_character(self, character_id: str, updates: Dict) -> Optional[CharacterProfile]:
        """更新角色信息"""
        data = self._load_json(self.characters_file)
        if character_id in data:
            data[character_id].update(updates)
            self._save_json(self.characters_file, data)
            return CharacterProfile.from_dict(data[character_id])
        return None
    
    def delete_character(self, character_id: str) -> bool:
        """删除角色"""
        data = self._load_json(self.characters_file)
        if character_id in data:
            del data[character_id]
            self._save_json(self.characters_file, data)
            return True
        return False
    
    def search_characters(self, query: str) -> List[CharacterProfile]:
        """搜索角色"""
        all_chars = self.get_all_characters()
        query_lower = query.lower()
        results = []
        
        for char in all_chars:
            # 搜索名称、身份、性格总结
            if (query_lower in char.name.lower() or
                query_lower in char.identity.lower() or
                query_lower in char.personality_summary.lower() or
                query_lower in char.book_title.lower()):
                results.append(char)
        
        return results
    
    # ==================== 角色组管理 ====================
    
    def create_group(self, name: str, description: str = "", character_ids: List[str] = None) -> Dict:
        """创建角色组"""
        groups = self._load_json(self.groups_file)
        
        group_id = str(uuid.uuid4())[:8]
        group = {
            "id": group_id,
            "name": name,
            "description": description,
            "character_ids": character_ids or [],
            "created_at": datetime.now().isoformat()
        }
        
        groups[group_id] = group
        self._save_json(self.groups_file, groups)
        return group
    
    def get_group(self, group_id: str) -> Optional[Dict]:
        """获取角色组"""
        groups = self._load_json(self.groups_file)
        return groups.get(group_id)
    
    def get_all_groups(self) -> List[Dict]:
        """获取所有角色组"""
        groups = self._load_json(self.groups_file)
        return list(groups.values())
    
    def add_to_group(self, group_id: str, character_id: str) -> bool:
        """添加角色到组"""
        groups = self._load_json(self.groups_file)
        if group_id in groups:
            if character_id not in groups[group_id]["character_ids"]:
                groups[group_id]["character_ids"].append(character_id)
                self._save_json(self.groups_file, groups)
            return True
        return False
    
    def remove_from_group(self, group_id: str, character_id: str) -> bool:
        """从组中移除角色"""
        groups = self._load_json(self.groups_file)
        if group_id in groups:
            if character_id in groups[group_id]["character_ids"]:
                groups[group_id]["character_ids"].remove(character_id)
                self._save_json(self.groups_file, groups)
            return True
        return False
    
    def delete_group(self, group_id: str) -> bool:
        """删除角色组"""
        groups = self._load_json(self.groups_file)
        if group_id in groups:
            del groups[group_id]
            self._save_json(self.groups_file, groups)
            return True
        return False
    
    def get_group_characters(self, group_id: str) -> List[CharacterProfile]:
        """获取组内所有角色"""
        group = self.get_group(group_id)
        if not group:
            return []
        
        characters = []
        for char_id in group["character_ids"]:
            char = self.get_character(char_id)
            if char:
                characters.append(char)
        return characters
    
    # ==================== 书库管理 ====================
    
    def add_book(self, title: str, author: str = "", file_path: str = "") -> Dict:
        """添加书籍"""
        books = self._load_json(self.books_file)
        
        book_id = str(uuid.uuid4())[:8]
        book = {
            "id": book_id,
            "title": title,
            "author": author,
            "file_path": file_path,
            "character_count": 0,
            "created_at": datetime.now().isoformat()
        }
        
        books[book_id] = book
        self._save_json(self.books_file, books)
        return book
    
    def get_book(self, book_id: str) -> Optional[Dict]:
        """获取书籍信息"""
        books = self._load_json(self.books_file)
        return books.get(book_id)
    
    def get_all_books(self) -> List[Dict]:
        """获取所有书籍"""
        books = self._load_json(self.books_file)
        return list(books.values())
    
    def update_book_character_count(self, book_id: str):
        """更新书籍的角色数量"""
        books = self._load_json(self.books_file)
        if book_id in books:
            characters = self.get_characters_by_book(book_id)
            books[book_id]["character_count"] = len(characters)
            self._save_json(self.books_file, books)
    
    def delete_book(self, book_id: str, delete_characters: bool = False) -> bool:
        """删除书籍"""
        books = self._load_json(self.books_file)
        if book_id in books:
            del books[book_id]
            self._save_json(self.books_file, books)
            
            if delete_characters:
                # 删除该书的所有角色
                characters = self.get_characters_by_book(book_id)
                for char in characters:
                    self.delete_character(char.id)
            
            return True
        return False
    
    # ==================== 导出/导入 ====================
    
    def export_character(self, character_id: str) -> Optional[Dict]:
        """导出一个角色的完整数据"""
        char = self.get_character(character_id)
        if char:
            return char.to_dict()
        return None
    
    def import_character(self, character_data: Dict) -> CharacterProfile:
        """导入角色数据"""
        # 生成新ID避免冲突
        if "id" in character_data:
            del character_data["id"]
        character_data["id"] = str(uuid.uuid4())[:8]
        
        character = CharacterProfile.from_dict(character_data)
        return self.add_character(character)


# 全局数据库实例
db = CharacterDatabase()
