"""Tests for Q&A endpoints."""
import pytest
from app.models.qa import Question, Answer, QuestionStatus
from app.models.user import User


class TestQAEndpoints:
    """Test Q&A API endpoints."""
    
    @pytest.fixture
    def sample_question(self, db_session, test_user):
        """Create a sample question."""
        question = Question(
            user_id=test_user.id,
            title="What are the best universities in Dhaka?",
            content="I'm looking for recommendations for good universities in Dhaka for Computer Science.",
            category="admissions",
            tags=["university", "dhaka", "computer-science"],
            status=QuestionStatus.OPEN
        )
        db_session.add(question)
        db_session.commit()
        db_session.refresh(question)
        return question
    
    def test_create_question(self, client, auth_headers):
        """Test creating a question."""
        response = client.post(
            "/api/v1/qa/questions",
            headers=auth_headers,
            json={
                "title": "How to apply for medical colleges?",
                "content": "What is the admission process for medical colleges in Bangladesh?",
                "category": "admissions",
                "tags": ["medical", "admission"]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "How to apply for medical colleges?"
        assert data["status"] == "open"
    
    def test_list_questions(self, client, sample_question):
        """Test listing questions."""
        response = client.get("/api/v1/qa/questions")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    def test_get_question_detail(self, client, sample_question):
        """Test getting question with answers."""
        response = client.get(f"/api/v1/qa/questions/{sample_question.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "What are the best universities in Dhaka?"
        assert "answers" in data
    
    def test_get_nonexistent_question(self, client):
        """Test getting non-existent question."""
        response = client.get("/api/v1/qa/questions/99999")
        
        assert response.status_code == 404
    
    def test_create_answer(self, client, auth_headers, sample_question):
        """Test answering a question."""
        response = client.post(
            f"/api/v1/qa/questions/{sample_question.id}/answers",
            headers=auth_headers,
            json={
                "content": "Some of the best universities in Dhaka include DU, BUET, and NSU."
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert data["question_id"] == sample_question.id
    
    def test_accept_answer(self, client, auth_headers, test_user, sample_question, db_session):
        """Test accepting an answer as best answer."""
        # First create an answer
        answer = Answer(
            question_id=sample_question.id,
            user_id=test_user.id,  # Different user answers
            content="Test answer",
            status="approved"
        )
        db_session.add(answer)
        db_session.commit()
        db_session.refresh(answer)
        
        response = client.post(
            f"/api/v1/qa/answers/{answer.id}/accept",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert "accepted" in response.json()["message"]
    
    def test_vote_answer(self, client, auth_headers, sample_question, db_session, test_user):
        """Test voting on an answer."""
        # Create an answer
        answer = Answer(
            question_id=sample_question.id,
            user_id=test_user.id,
            content="Test answer for voting",
            status="approved"
        )
        db_session.add(answer)
        db_session.commit()
        db_session.refresh(answer)
        
        response = client.post(
            f"/api/v1/qa/answers/{answer.id}/vote?is_upvote=true",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "upvote_count" in data


class TestCommentEndpoints:
    """Test comment system."""
    
    def test_create_comment(self, client, auth_headers):
        """Test creating a comment."""
        response = client.post(
            "/api/v1/comments/comments",
            headers=auth_headers,
            json={
                "content": "This is a helpful answer, thanks!",
                "content_type": "answer",
                "content_id": 1
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "This is a helpful answer, thanks!"
        assert data["content_type"] == "answer"
    
    def test_list_comments(self, client):
        """Test listing comments for content."""
        response = client.get("/api/v1/comments/comments/answer/1")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_like_comment(self, client, auth_headers):
        """Test liking a comment."""
        # First create a comment
        create_response = client.post(
            "/api/v1/comments/comments",
            headers=auth_headers,
            json={
                "content": "Test comment for liking",
                "content_type": "institution",
                "content_id": 1
            }
        )
        
        comment_id = create_response.json()["id"]
        
        # Like the comment
        response = client.post(
            f"/api/v1/comments/comments/{comment_id}/like",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "like_count" in data
