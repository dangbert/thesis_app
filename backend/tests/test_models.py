from app.models.User import User


def test_user(session):
    email = "testuser@example.com"
    user = User(email=email)
    session.add(user)
    session.commit()

    print("created user: ", user.id)
    assert user.email_verified == False
    assert isinstance(user.id, UUID)
    # assert user.email_token != None
    assert user.email == email
    # assert user.email_token != None
