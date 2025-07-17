from PyQt5.QtWidgets import QListWidgetItem

class IndexQListWidgetItem(QListWidgetItem):
    """带索引的列表项"""
    
    def __init__(self, name: str, index: int):
        super().__init__(name)
        self.index = index
    
    def get_index(self) -> int:
        return self.index