import json
def note_aad(student_id,note_id,algorithm,key_id):
    return json.dumps(dict(version=1,student_id=str(student_id),note_id=str(note_id),algorithm=algorithm,key_id=str(key_id)),sort_keys=True,separators=(',',':')).encode()
