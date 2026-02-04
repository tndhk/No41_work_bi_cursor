"""テスト用セットアップAPIルート"""
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.services.user_service import create_user
from app.services.dataset_service import create_dataset_from_local_csv
from app.services.card_service import create_card
from app.services.dashboard_service import create_dashboard
from app.models.user import UserCreate
from app.models.card import CardCreate
from app.models.dashboard import DashboardCreate

router = APIRouter(prefix="/test", tags=["test"])


class TestSetupResponse(BaseModel):
    email: str
    password: str
    dashboard_id: str
    dashboard_name: str
    filter_name: str


@router.post("/setup", response_model=TestSetupResponse)
async def setup_test_data():
    """テスト用データセットアップ（テスト環境のみ）"""
    if not settings.allow_test_setup or settings.env == "prod":
        raise HTTPException(
            status_code=403,
            detail="Test setup endpoint is disabled. Set ALLOW_TEST_SETUP=true to enable."
        )
    
    # テストユーザーを作成
    test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    test_password = "TestPassword123"
    user = await create_user(UserCreate(
        email=test_email,
        name="Test User",
        password=test_password,
    ))
    
    # テスト用CSVデータを作成
    csv_content = """category,date,value
A,2024-01-01,100
A,2024-01-02,150
B,2024-01-01,200
B,2024-01-02,250
""".encode('utf-8')
    
    # データセットを作成
    dataset = await create_dataset_from_local_csv(
        user_id=user.user_id,
        name="Test Dataset",
        csv_content=csv_content,
        encoding="utf-8",
        delimiter=",",
        has_header=True,
    )
    
    # カードを作成
    card_code = """
def render(dataset, filters, params):
    category = filters.get('category', 'A')
    total = dataset['value'].sum()
    html = f'<div style="padding: 20px; background: #f5f5f5; border-radius: 8px;"><h3>Category: {category}</h3><p>Total Value: {total}</p></div>'
    return {
        "html": html,
        "used_columns": ["category", "value"],
        "filter_applicable": ["category"],
    }
"""
    card = await create_card(
        user_id=user.user_id,
        card_data=CardCreate(
            name="Test Card",
            dataset_id=dataset.dataset_id,
            code=card_code,
            params={},
            used_columns=["category", "value"],
            filter_applicable=["category"],
        ),
    )
    
    # ダッシュボードを作成
    filter_name = "category"
    dashboard = await create_dashboard(
        user_id=user.user_id,
        dashboard_data=DashboardCreate(
            name="Test Dashboard",
            layout={
                "cards": [
                    {
                        "cardId": card.card_id,
                        "x": 0,
                        "y": 0,
                        "w": 4,
                        "h": 3,
                    }
                ]
            },
            filters=[
                {
                    "name": filter_name,
                    "type": "category",
                    "column": "category",
                }
            ],
        ),
    )
    
    return TestSetupResponse(
        email=test_email,
        password=test_password,
        dashboard_id=dashboard.dashboard_id,
        dashboard_name=dashboard.name,
        filter_name=filter_name,
    )
