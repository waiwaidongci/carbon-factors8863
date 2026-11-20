from sqlalchemy import Column,Integer,String,JSON,Text,Float,Boolean
from src.config.database import Base
class Scenario(Base):
 __tablename__='reduction_scenarios'
 id=Column(Integer,primary_key=True); name=Column(String(120),unique=True); target_kg=Column(Float); created=Column(Float)
class Measure(Base):
 __tablename__='reduction_measures'
 id=Column(Integer,primary_key=True); name=Column(String(120)); cost=Column(Float); prereq=Column(JSON); ratios=Column(JSON); created=Column(Float)
class Catalog(Base):
 __tablename__='reduction_catalog'
 id=Column(Integer,primary_key=True); version=Column(Integer,default=1)
class Plan(Base):
 __tablename__='reduction_plans'
 id=Column(Integer,primary_key=True); request_key=Column(String(64),unique=True); name=Column(String(120)); run_id=Column(Integer); catalog_version=Column(Integer); budget_seconds=Column(Float); status=Column(String(20)); outcome=Column(String(20)); input=Column(JSON); progress=Column(JSON); result=Column(JSON); error=Column(Text); effective=Column(Boolean,default=False); created=Column(Float); published=Column(Float)
