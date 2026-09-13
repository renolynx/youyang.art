"""Regression checks for shared cards, stale drafts and a failed release."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from content_model import card, collections, migrate, validate
from desk_store import Store, Conflict, encoded

ROOT=Path(__file__).resolve().parent.parent

class ContentModelTests(unittest.TestCase):
    def test_upload_caps_the_long_edge_for_portraits(self):
        from optimize import fit
        self.assertEqual(fit(2000,4000,1800),(900,1800))
        self.assertEqual(fit(4000,2000,1800),(1800,900))
        self.assertEqual(fit(320,240,1800),(320,240))

    def test_existing_migration_preserves_every_card(self):
        original=json.loads((ROOT/'_src/test_fixtures/legacy-card-content.json').read_text())
        updated=migrate(original)
        old=list(collections(original));new=list(collections(updated))
        self.assertEqual(len(old),len(new))
        count=0
        for (_,lang,items),(_,_,refs) in zip(old,new):
            for item,ref in zip(items,refs):
                result=card(ref,updated['pages'],lang)
                for k,v in item.items(): self.assertEqual(v,result.get(k),(k,item))
                count+=1
        self.assertGreater(count,40)
        self.assertEqual(migrate(updated),updated)
    def test_shared_cover_and_year_flow_into_both_languages(self):
        doc=json.loads((ROOT/'_src/content/site.json').read_text());p=next(p for p in doc['pages'] if p['slug']=='inside-my-eyes')
        p['cover']='media/replacement.jpg';p['year']='2027';p['title']='Updated title'
        for lang in ('en','zh'):
            resolved=card({'ref':p['id']},doc['pages'],lang)
            self.assertEqual(resolved['cover'],'media/replacement.jpg');self.assertEqual(resolved['meta'],'2027')
        self.assertEqual(card({'ref':p['id']},doc['pages'])['title'],'Updated title')
    def test_missing_reference_and_duplicate_slug_rejected(self):
        doc=json.loads((ROOT/'_src/content/site.json').read_text())
        with self.assertRaises(ValueError): card({'ref':'absent'},doc['pages'])
        doc['pages'].append(doc['pages'][0])
        with self.assertRaises(ValueError): validate(doc)

class DraftTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        (self.root/'_src/content').mkdir(parents=True)
        shutil.copy(ROOT/'_src/content/site.json',self.root/'_src/content/site.json')
        self.store=Store(self.root)
    def tearDown(self): self.temp.cleanup()
    def save_changed(self):
        current=self.store.read();draft=copy.deepcopy(current['site']);draft['pages'][0]['description']='saved draft'
        return self.store.save(draft,current['revision'],current['sourceRevision'])
    def test_stale_save_cannot_overwrite_other_tab(self):
        old=self.store.read();saved=self.save_changed()
        with self.assertRaises(Conflict): self.store.save(old['site'],old['revision'],old['sourceRevision'])
        self.assertEqual(self.store.read()['revision'],saved['revision'])
        self.assertNotIn('saved draft',self.store.source.read_text())
    def test_external_source_change_preserves_draft(self):
        saved=self.save_changed();self.store.source.write_bytes(self.store.source.read_bytes()+b' ')
        with self.assertRaises(Conflict):self.store.save(saved['site'],saved['revision'],saved['sourceRevision'])
        self.assertEqual(self.store.read()['site']['pages'][0]['description'],'saved draft')
    def test_invalid_input_preserves_previous_draft(self):
        saved=self.save_changed();bad=copy.deepcopy(saved['site']);bad['pages'][0]['title']=''
        with self.assertRaises(ValueError): self.store.save(bad,saved['revision'],saved['sourceRevision'])
        self.assertEqual(self.store.read()['revision'],saved['revision'])
    def test_build_failure_does_not_change_public_source(self):
        saved=self.save_changed();before=self.store.source.read_bytes()
        for folder in ('assets','media'):(self.root/folder).mkdir()
        with patch.object(self.store,'command',side_effect=RuntimeError('build failed')):
            with self.assertRaises(RuntimeError):self.store.release(saved['revision'],push=False)
        self.assertEqual(self.store.source.read_bytes(),before)
        self.assertEqual(self.store.read()['revision'],saved['revision'])
    def test_reloading_source_keeps_unsaved_input_in_history(self):
        saved=self.save_changed();unsaved=copy.deepcopy(saved['site']);unsaved['pages'][0]['description']='not saved yet'
        fresh=self.store.reload_source(saved['revision'],unsaved)
        self.assertNotEqual(fresh['site']['pages'][0]['description'],'not saved yet')
        snapshots=[json.loads(p.read_text()) for p in (self.store.private/'history').glob('*.json')]
        self.assertTrue(any(x['site']['pages'][0]['description']=='not saved yet' for x in snapshots))
    def test_existing_addresses_cannot_be_deleted(self):
        saved=self.store.read();bad=copy.deepcopy(saved['site']);bad['pages']=bad['pages'][1:]
        with self.assertRaises(ValueError):self.store.save(bad,saved['revision'],saved['sourceRevision'])

if __name__=='__main__':unittest.main()
