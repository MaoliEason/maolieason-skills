import hashlib,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from PIL import Image,ImageDraw
SKILL=Path(__file__).resolve().parents[1]; SCRIPT=SKILL/"scripts"/"release_gate.py"
sys.path.insert(0,str(SKILL/"scripts")); from release_gate import GateError,validate
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
class GateTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory(); self.r=Path(self.t.name)
  for d in ("in","work","qa","dist"): (self.r/d).mkdir()
  b=Image.new("RGB",(80,60),(20,30,40)); b.save(self.r/"in/base.png")
  Image.new("RGB",(20,20),(1,2,3)).save(self.r/"in/src.png"); Image.new("RGB",(20,20),(4,5,6)).save(self.r/"work/adapt.png")
  Image.new("RGB",(40,20)).save(self.r/"qa/evidence.png")
  mask=Image.new("L",(80,60),0); ImageDraw.Draw(mask).rectangle((20,15,44,39),fill=255); mask.save(self.r/"qa/mask.png")
  c=b.copy(); ImageDraw.Draw(c).rectangle((20,15,44,39),fill=(200,100,20)); c.save(self.r/"work/candidate.png")
  pts=[[20,15],[44,15],[20,39],[44,39]]
  self.m={"schema_version":1,"task_id":"test","inputs":{k:{"path":p,"sha256":sha(self.r/p)} for k,p in {"base_image":"in/base.png","source_module":"in/src.png","adapted_module":"work/adapt.png","editable_mask":"qa/mask.png","candidate_image":"work/candidate.png","review_evidence":"qa/evidence.png"}.items()},"geometry":{"base_camera_id":"cam","adapted_module_camera_id":"cam","fit_anchors":[{"expected_px":p,"actual_px":p} for p in pts],"holdout_anchors":[{"expected_px":p,"actual_px":p} for p in ([32,15],[44,22])],"fit_rms_limit_px":2,"holdout_rms_limit_px":3,"max_edge_error_px":2,"max_connection_gap_px":2,"minimum_upper_exit_clearance_px":8,"platform_edge_max_error_px":1,"wall_joint_max_error_px":1,"stair_top_gap_px":0,"stair_bottom_gap_px":0,"upper_exit_clearance_px":12},"structure_checks":{k:True for k in ("platform_edge_aligned","wall_joint_aligned","stair_top_connected","stair_bottom_connected","upper_exit_clear","railing_does_not_block_exit")}}
  self.save()
 def tearDown(self): self.t.cleanup()
 def save(self): (self.r/"manifest.json").write_text(json.dumps(self.m))
 def refresh(self,k,p): self.m["inputs"][k]["sha256"]=sha(self.r/p); self.save()
 def test_candidate_is_not_final(self): self.assertFalse(validate(self.r/"manifest.json")["release_allowed"])
 def test_frozen_pixel_change_blocks(self):
  p=self.r/"work/candidate.png"; im=Image.open(p).convert("RGB"); im.putpixel((2,2),(255,0,0)); im.save(p); self.refresh("candidate_image","work/candidate.png")
  with self.assertRaisesRegex(GateError,"frozen-region"): validate(self.r/"manifest.json")
 def test_stale_hash_blocks(self):
  self.m["inputs"]["base_image"]["sha256"]="0"*64; self.save()
  with self.assertRaisesRegex(GateError,"SHA-256"): validate(self.r/"manifest.json")
 def test_camera_mismatch_blocks(self):
  self.m["geometry"]["adapted_module_camera_id"]="wrong"; self.save()
  with self.assertRaisesRegex(GateError,"camera IDs"): validate(self.r/"manifest.json")
 def test_missing_holdout_blocks(self):
  self.m["geometry"]["holdout_anchors"]=[]; self.save()
  with self.assertRaisesRegex(GateError,"at least 2"): validate(self.r/"manifest.json")
 def test_bad_holdout_blocks(self):
  self.m["geometry"]["holdout_anchors"][0]["actual_px"]=[100,100]; self.save()
  with self.assertRaisesRegex(GateError,"held-out anchor"): validate(self.r/"manifest.json")
 def test_structure_failure_blocks(self):
  self.m["structure_checks"]["upper_exit_clear"]=False; self.save()
  with self.assertRaisesRegex(GateError,"upper_exit_clear"): validate(self.r/"manifest.json")
 def test_nonbinary_mask_blocks(self):
  p=self.r/"qa/mask.png"; im=Image.open(p).convert("L"); im.putpixel((0,0),128); im.save(p); self.refresh("editable_mask","qa/mask.png")
  with self.assertRaisesRegex(GateError,"binary"): validate(self.r/"manifest.json")
 def test_size_mismatch_blocks(self):
  Image.new("RGB",(79,60)).save(self.r/"work/candidate.png"); self.refresh("candidate_image","work/candidate.png")
  with self.assertRaisesRegex(GateError,"dimensions"): validate(self.r/"manifest.json")
 def test_release_needs_human_approval(self):
  a=self.r/"approval.json"; a.write_text(json.dumps({"approved":True}))
  out=self.r/"dist/final.png"; p=subprocess.run([sys.executable,str(SCRIPT),"release","--manifest",str(self.r/"manifest.json"),"--approval",str(a),"--output",str(out)],capture_output=True)
  self.assertNotEqual(p.returncode,0); self.assertFalse(out.exists())
 def test_release_binds_candidate_hash(self):
  a=self.r/"approval.json"; a.write_text(json.dumps({"schema_version":1,"approved":True,"reviewer_type":"human","reviewer":"owner","candidate_sha256":sha(self.r/"work/candidate.png"),"reviewed_at":"2026-10-23T12:00:00+08:00"}))
  out=self.r/"dist/final.png"; p=subprocess.run([sys.executable,str(SCRIPT),"release","--manifest",str(self.r/"manifest.json"),"--approval",str(a),"--output",str(out)],capture_output=True,text=True)
  self.assertEqual(p.returncode,0,p.stdout+p.stderr); self.assertEqual(sha(out),sha(self.r/"work/candidate.png"))
 def test_release_refuses_overwrite(self):
  out=self.r/"dist/final.png"; out.write_bytes(b"keep")
  a=self.r/"approval.json"; a.write_text(json.dumps({"schema_version":1,"approved":True,"reviewer_type":"human","reviewer":"owner","candidate_sha256":sha(self.r/"work/candidate.png"),"reviewed_at":"2026-10-23T12:00:00+08:00"}))
  p=subprocess.run([sys.executable,str(SCRIPT),"release","--manifest",str(self.r/"manifest.json"),"--approval",str(a),"--output",str(out)],capture_output=True)
  self.assertNotEqual(p.returncode,0); self.assertEqual(out.read_bytes(),b"keep")
if __name__=="__main__": unittest.main()
