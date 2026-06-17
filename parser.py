import json
import os
import csv
import logging
from datetime import datetime
from typing import List, Dict, Optional
from config import MEMBERS_FILE

# Setup logging
logger = logging.getLogger(__name__)

class MembersParser:
    """Класс для парсинга и управления участниками Telegram групп/каналов"""
    
    def __init__(self):
        self.members_file = MEMBERS_FILE
        self.members = self._load_members()
    
    def _load_members(self) -> Dict[str, List[Dict]]:
        """Загрузить участников из JSON файла"""
        if not os.path.exists(self.members_file):
            return {}
        
        try:
            with open(self.members_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"Ошибка при чтении {self.members_file}, создаю новый файл")
            return {}
    
    def _save_members(self):
        """Сохранить участников в JSON файл"""
        with open(self.members_file, 'w', encoding='utf-8') as f:
            json.dump(self.members, f, ensure_ascii=False, indent=2)
        logger.info(f"Участники сохранены в {self.members_file}")
    
    async def parse_group(self, client, group_id: int, group_name: str = None) -> int:
        """
        Парсить всех участников группы/канала
        
        Args:
            client: Telethon client
            group_id: ID группы или канала
            group_name: Имя группы для сохранения (опционально)
        
        Returns:
            Количество добавленных участников
        """
        try:
            # Получить объект группы
            entity = await client.get_entity(group_id)
            
            if group_name is None:
                group_name = entity.title if hasattr(entity, 'title') else str(group_id)
            
            logger.info(f"Начинаю парсинг группы '{group_name}' (ID: {group_id})")
            
            # Инициализировать список участников для группы
            if group_name not in self.members:
                self.members[group_name] = []
            
            # Получить список участников
            participants = await client.get_participants(entity)
            
            # Существующие user_ids для избежания дубликатов
            existing_ids = {m['user_id'] for m in self.members[group_name]}
            
            new_members = 0
            for participant in participants:
                user_id = participant.id
                
                # Пропустить, если уже существует
                if user_id in existing_ids:
                    continue
                
                member_data = {
                    'user_id': user_id,
                    'first_name': participant.first_name or '',
                    'last_name': participant.last_name or '',
                    'username': participant.username or '',
                    'is_bot': participant.bot,
                    'is_self': participant.is_self,
                    'phone': participant.phone or '',
                    'status': str(participant.status) if participant.status else '',
                    'added_at': datetime.now().isoformat()
                }
                
                self.members[group_name].append(member_data)
                new_members += 1
            
            # Сохранить в файл
            self._save_members()
            
            logger.info(f"Добавлено {new_members} новых участников из '{group_name}'")
            logger.info(f"Всего участников в группе: {len(self.members[group_name])}")
            
            return new_members
        
        except Exception as e:
            logger.error(f"Ошибка при парсинге группы: {e}")
            raise
    
    def get_members(self, group_name: str) -> List[Dict]:
        """Получить список участников группы"""
        return self.members.get(group_name, [])
    
    def get_all_groups(self) -> List[str]:
        """Получить список всех групп"""
        return list(self.members.keys())
    
    def get_group_stats(self, group_name: str) -> Dict:
        """Получить статистику по группе"""
        members = self.get_members(group_name)
        
        if not members:
            return {'error': 'Группа не найдена'}
        
        return {
            'group_name': group_name,
            'total_members': len(members),
            'bots': sum(1 for m in members if m['is_bot']),
            'real_users': sum(1 for m in members if not m['is_bot']),
            'with_username': sum(1 for m in members if m['username']),
            'with_phone': sum(1 for m in members if m['phone']),
            'last_updated': members[-1]['added_at'] if members else None
        }
    
    def export_csv(self, group_name: str, output_file: str = None) -> str:
        """Экспортировать участников в CSV"""
        members = self.get_members(group_name)
        
        if not members:
            raise ValueError(f"Группа '{group_name}' не найдена")
        
        if output_file is None:
            output_file = f"{group_name}_members.csv"
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['user_id', 'first_name', 'last_name', 'username', 'is_bot', 'phone']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            writer.writeheader()
            for member in members:
                writer.writerow({k: member.get(k, '') for k in fieldnames})
        
        logger.info(f"Экспортировано {len(members)} участников в {output_file}")
        return output_file
    
    def clear_group(self, group_name: str) -> bool:
        """Очистить список участников группы"""
        if group_name in self.members:
            del self.members[group_name]
            self._save_members()
            logger.info(f"Группа '{group_name}' очищена")
            return True
        return False
    
    def get_member_by_username(self, group_name: str, username: str) -> Optional[Dict]:
        """Найти участника по username"""
        members = self.get_members(group_name)
        for member in members:
            if member['username'].lower() == username.lower():
                return member
        return None
