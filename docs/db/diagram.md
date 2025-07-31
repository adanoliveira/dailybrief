# DailyBrief Database Diagram

## Visualization

The database schema can be visualized using [dbdiagram.io](https://dbdiagram.io).

## Steps to Generate the Diagram

1. Go to [dbdiagram.io](https://dbdiagram.io)
2. Click "Create New Diagram"
3. Copy the DBML code below into the editor
4. The diagram will be generated automatically
5. Adjust the layout as needed by dragging tables

## DBML Code

```dbml
// DailyBrief Database Schema

// Django auth tables
Table auth_user {
  id integer [pk, increment]
  username varchar [not null]
  email varchar
  password varchar
  is_active boolean
  date_joined timestamp
  last_login timestamp
  is_staff boolean
  is_superuser boolean
}

// Core models - Article Domain
Table articles_storygroup {
  id integer [pk, increment]
  public_id uuid [unique, not null]
  title varchar [not null]
  summary text
  start_date timestamp [not null]
  end_date timestamp
  is_ongoing boolean [default: true]
  created_at timestamp [not null]
  updated_at timestamp [not null]
}

Table articles_article {
  id integer [pk, increment]
  public_id uuid [unique, not null]
  title varchar(512) [not null]
  description text
  content text
  url varchar(1024) [not null]
  image_url varchar(1024)
  source_name varchar(255)
  author varchar(255)
  published_at timestamp [not null]
  fetched_at timestamp [not null]
  updated_at timestamp [not null]
  keywords varchar[] 
  word_count integer
  read_time_minutes float
  content_hash varchar(64)
  sentiment_score float
  entities json
  popularity_score float [default: 0.0]
  relevance_score float [default: 0.0]
  is_top_headline boolean [default: false]
  summary_ready boolean [default: false]
  publication_id integer [ref: > feeds_publication.id]
  language_id integer [ref: > feeds_language.id]
  story_group_id integer [ref: > articles_storygroup.id]
}

Table articles_userarticleinteraction {
  id integer [pk, increment]
  user_id integer [ref: > auth_user.id, not null]
  article_id integer [ref: > articles_article.id, not null]
  read boolean [default: false]
  read_at timestamp
  bookmarked boolean [default: false]
  bookmarked_at timestamp
  clicked boolean [default: false]
  clicked_at timestamp
  created_at timestamp [not null]
  updated_at timestamp [not null]
  
  indexes {
    (user_id, article_id) [unique]
    (user_id, read)
    (user_id, bookmarked)
  }
}

// Feed-related models - Feeds Domain
Table feeds_topic {
  id integer [pk, increment]
  name varchar(100) [not null, unique]
  slug varchar(100) [unique]
  created_at timestamp [not null]
}

Table feeds_region {
  id integer [pk, increment]
  code varchar(5) [unique]
  name varchar(100) [not null]
  created_at timestamp [not null]
}

Table feeds_language {
  id integer [pk, increment]
  iso_code varchar(5) [unique]
  name varchar(100) [not null]
  created_at timestamp [not null]
}

Table feeds_publication {
  id integer [pk, increment]
  name varchar(255) [not null]
  news_api_id varchar(255)
  rss_url varchar(255)
  website_url varchar(255) [not null]
  logo_url varchar(255)
  description text
  authority float [default: 1.0]
  created_at timestamp [not null]
  updated_at timestamp [not null]
}

Table feeds_usertopic {
  id integer [pk, increment]
  user_id integer [ref: > auth_user.id, not null]
  topic_id integer [ref: > feeds_topic.id, not null]
  weight float [default: 1.0]
  created_at timestamp [not null]
  
  indexes {
    (user_id, topic_id) [unique]
  }
}

Table feeds_userpublication {
  id integer [pk, increment]
  user_id integer [ref: > auth_user.id, not null]
  publication_id integer [ref: > feeds_publication.id, not null]
  weight float [default: 1.0]
  created_at timestamp [not null]
  
  indexes {
    (user_id, publication_id) [unique]
  }
}

Table feeds_userregion {
  id integer [pk, increment]
  user_id integer [ref: > auth_user.id, not null]
  region_id integer [ref: > feeds_region.id, not null]
  weight float [default: 1.0]
  created_at timestamp [not null]
  
  indexes {
    (user_id, region_id) [unique]
  }
}

Table feeds_userlanguage {
  id integer [pk, increment]
  user_id integer [ref: > auth_user.id, not null]
  language_id integer [ref: > feeds_language.id, not null]
  weight float [default: 1.0]
  created_at timestamp [not null]
  
  indexes {
    (user_id, language_id) [unique]
  }
}

// Summariser Domain
Table summariser_articlesummary {
  id integer [pk, increment]
  article_id integer [ref: > articles_article.id, not null]
  abstract text
  key_points text
  full_summary text
  is_translated boolean [default: false]
  original_language varchar(5)
  ai_provider varchar(50)
  prompt_tokens integer [default: 0]
  completion_tokens integer [default: 0]
  processing_time float [default: 0.0]
  created_at timestamp [not null]
  updated_at timestamp [not null]
}

Table summariser_summarizationrequest {
  id integer [pk, increment]
  article_id integer [ref: > articles_article.id, not null]
  status varchar(20) [default: 'pending']
  attempts integer [default: 0]
  max_attempts integer [default: 3]
  last_error text
  created_at timestamp [not null]
  updated_at timestamp [not null]
  completed_at timestamp
  
  indexes {
    (status)
    (article_id, status)
  }
}

// Digest Domain
Table digest_digest {
  id integer [pk, increment]
  public_id uuid [unique, not null]
  user_id integer [ref: > auth_user.id, not null]
  title varchar(255) [not null]
  date date [not null]
  introduction text
  html_content text
  is_published boolean [default: false]
  is_sent boolean [default: false]
  sent_at timestamp
  created_at timestamp [not null]
  updated_at timestamp [not null]
  
  indexes {
    (user_id, date) [unique]
    (public_id)
  }
}

Table digest_digeststory {
  id integer [pk, increment]
  digest_id integer [ref: > digest_digest.id, not null]
  title varchar(255) [not null]
  summary text
  order integer [default: 0]
  created_at timestamp [not null]
  updated_at timestamp [not null]
}

// Notifications Domain
Table notifications_usernotificationsettings {
  id integer [pk, increment]
  user_id integer [ref: > auth_user.id, not null]
  email_digest boolean [default: true]
  email_news_updates boolean [default: false]
  push_enabled boolean [default: true]
  push_digest boolean [default: true]
  push_news_updates boolean [default: false]
  preferred_time time [default: '08:00']
  created_at timestamp [not null]
  updated_at timestamp [not null]
}

Table notifications_pushsubscription {
  id integer [pk, increment]
  user_id integer [ref: > auth_user.id, not null]
  endpoint varchar(500) [not null]
  p256dh varchar(255) [not null]
  auth varchar(255) [not null]
  browser varchar(100)
  device varchar(100)
  is_active boolean [default: true]
  created_at timestamp [not null]
  last_used timestamp [not null]
  
  indexes {
    (user_id, endpoint) [unique]
  }
}

Table notifications_notification {
  id integer [pk, increment]
  public_id uuid [unique, not null]
  user_id integer [ref: > auth_user.id, not null]
  notification_type varchar(20) [not null]
  title varchar(255) [not null]
  body text
  action_url varchar(255)
  email_sent boolean [default: false]
  push_sent boolean [default: false]
  in_app_shown boolean [default: false]
  status varchar(20) [default: 'pending']
  error_message text
  created_at timestamp [not null]
  sent_at timestamp
  read_at timestamp
  
  indexes {
    (created_at)
    (user_id, status)
    (public_id)
  }
}

// Accounts Domain
Table accounts_userprofile {
  id integer [pk, increment]
  user_id integer [ref: > auth_user.id, not null]
  public_id uuid [unique, not null]
  timezone varchar(50) [default: 'UTC']
  onboarding_completed boolean [default: false]
  created_at timestamp [not null]
  updated_at timestamp [not null]
}

// Many-to-many relationships
Table articles_article_topics {
  id integer [pk, increment]
  article_id integer [ref: > articles_article.id, not null]
  topic_id integer [ref: > feeds_topic.id, not null]
  
  indexes {
    (article_id, topic_id) [unique]
  }
}

Table articles_article_regions {
  id integer [pk, increment]
  article_id integer [ref: > articles_article.id, not null]
  region_id integer [ref: > feeds_region.id, not null]
  
  indexes {
    (article_id, region_id) [unique]
  }
}

Table articles_article_related_articles {
  id integer [pk, increment]
  from_article_id integer [ref: > articles_article.id, not null]
  to_article_id integer [ref: > articles_article.id, not null]
  
  indexes {
    (from_article_id, to_article_id) [unique]
  }
}

Table feeds_publication_topics {
  id integer [pk, increment]
  publication_id integer [ref: > feeds_publication.id, not null]
  topic_id integer [ref: > feeds_topic.id, not null]
  
  indexes {
    (publication_id, topic_id) [unique]
  }
}

Table feeds_publication_languages {
  id integer [pk, increment]
  publication_id integer [ref: > feeds_publication.id, not null]
  language_id integer [ref: > feeds_language.id, not null]
  
  indexes {
    (publication_id, language_id) [unique]
  }
}

Table feeds_publication_regions {
  id integer [pk, increment]
  publication_id integer [ref: > feeds_publication.id, not null]
  region_id integer [ref: > feeds_region.id, not null]
  
  indexes {
    (publication_id, region_id) [unique]
  }
}

Table digest_digeststory_articles {
  id integer [pk, increment]
  digeststory_id integer [ref: > digest_digeststory.id, not null]
  article_id integer [ref: > articles_article.id, not null]
  
  indexes {
    (digeststory_id, article_id) [unique]
  }
}
```