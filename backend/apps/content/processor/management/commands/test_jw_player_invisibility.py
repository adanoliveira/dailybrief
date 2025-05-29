"""
Simple test to verify JW Player content is completely invisible to users.
Run with: ./docker.sh django shell < backend/test_jw_player_invisibility.py
"""

from apps.content.processor.algorithmic_processor import AlgorithmicProcessor

def test_jw_player_invisibility():
    processor = AlgorithmicProcessor()
    
    # Test HTML with JW Player
    test_html = '''<html><body><article>
    <h1>Test Article with JW Player</h1>
    <p>Paragraph before JW Player.</p>
    <div class="jwvideoplayer" id="player-test123" data-media-id="abc123" data-player="config456">
        <p>This JW Player content should be completely hidden from users</p>
        <span>No trace of this text should appear</span>
    </div>
    <p>Paragraph after JW Player.</p>
    <iframe src="https://www.youtube.com/embed/dQw4w9WgXcQ" width="560" height="315" allowfullscreen></iframe>
    <p>Final paragraph.</p>
    </article></body></html>'''
    
    # Process content
    result = processor.process_content(test_html, {
        'title': 'Test Article with JW Player',
        'url': 'https://test.com'
    })
    
    print("=== JW Player Invisibility Test ===")
    print(f"Processing successful: {result.success}")
    print(f"Total content blocks: {len(result.content_blocks)}")
    
    # Check for video blocks
    video_blocks = [b for b in result.content_blocks if b.type == 'video']
    print(f"Video blocks found: {len(video_blocks)}")
    
    # Check for JW Player traces in clean content
    jw_traces = [
        "jwvideoplayer", "JW Player content", "No trace of this text",
        "abc123", "config456", "player-test123"
    ]
    
    found_traces = []
    for trace in jw_traces:
        if trace.lower() in result.clean_content.lower():
            found_traces.append(trace)
    
    if found_traces:
        print(f"❌ FAIL: Found JW Player traces in content: {found_traces}")
        print(f"Clean content: {result.clean_content}")
    else:
        print("✅ SUCCESS: No JW Player traces found in clean content")
    
    # Check video types
    video_types = [b.metadata.get('video_type', 'unknown') for b in video_blocks]
    print(f"Video types found: {video_types}")
    
    # Verify no JW Player videos
    jwplayer_found = any('jwplayer' in vtype for vtype in video_types)
    if jwplayer_found:
        print("❌ FAIL: JW Player video block was created!")
    else:
        print("✅ SUCCESS: No JW Player video blocks created")
    
    # Check paragraphs
    paragraph_blocks = [b for b in result.content_blocks if b.type == 'paragraph']
    paragraph_contents = [b.content for b in paragraph_blocks]
    
    expected_paragraphs = [
        "Paragraph before JW Player",
        "Paragraph after JW Player", 
        "Final paragraph"
    ]
    
    found_paragraphs = []
    for expected in expected_paragraphs:
        if any(expected in content for content in paragraph_contents):
            found_paragraphs.append(expected)
    
    print(f"Expected paragraphs found: {len(found_paragraphs)}/{len(expected_paragraphs)}")
    
    if len(found_paragraphs) == len(expected_paragraphs):
        print("✅ SUCCESS: All expected paragraphs found, JW Player content properly hidden")
    else:
        print(f"❌ FAIL: Missing paragraphs. Found: {found_paragraphs}")
    
    print(f"\nContent blocks by type:")
    block_types = {}
    for block in result.content_blocks:
        block_types[block.type] = block_types.get(block.type, 0) + 1
    for block_type, count in block_types.items():
        print(f"  {block_type}: {count}")

# Run the test
test_jw_player_invisibility()