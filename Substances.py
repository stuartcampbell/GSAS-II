"""
*Substances: Define Materials*
---------------------------------------------------------------------------------

Defines materials commonly found in small angle & reflectometry experiments.
GSASII substances as a dictionary ''Substances.Substances'' with these materials.

Each entry in ''Substances'' consists of::

     'key':{'Elements':{element:{'Num':float number in formula},...},'Density':value, 'Volume':,value}

Density & Volume are optional, if one missing it is calculated from the other; if both
are missing then Volume is estimated from composition & assuming 10A^3 for each atom,
Density is calculated from that Volume.
See examples below for what is needed.
"""
Substances = {
'Alumina':{'Elements':{'Al':{'Num':2.},'O':{'Num':3.}},'Density':3.986,},
'Water':{'Elements':{'O':{'Num':1.},'H':{'Num':2.}},'Density':1.0},
'Silicon':{'Elements':{'Si':{'Num':8.}},'Volume':160.209},
'a-Quartz':{'Elements':{'Si':{'Num':3.},'O':{'Num':6.}},'Volume':113.057},
'Ethanol':{'Elements':{'C':{'Num':2.},'O':{'Num':1},'H':{'Num':6.}},},
'Polyethylene':{'Elements':{'C':{'Num':1.},'H':{'Num':2.}},'Density':0.93,},
'Polystyrene':{'Elements':{'C':{'Num':1.},'H':{'Num':1.}},'Density':1.060,},
'Teflon':{'Elements':{'C':{'Num':1.},'F':{'Num':2.}},'Density':2.25,},
'Mylar':{'Elements':{'C':{'Num':5.},'H':{'Num':4.},'O':{'Num':2.}},'Density':1.38,},
'Iron':{'Elements':{'Fe':{'Num':4.}},'Density':7.87,},
'FeO-wustite':{'Elements':{'Fe':{'Num':4.},'O':{'Num':4.}},'Volume':79.285},
'Fe2O3-hematite':{'Elements':{'Fe':{'Num':12.},'O':{'Num':18.}},'Volume':301.689},
'Fe3O4-magnetite':{'Elements':{'Fe':{'Num':24.},'O':{'Num':32.}},'Volume':591.921},
'Zirconium':{'Elements':{'Zr':{'Num':2.}},'Density':6.51,},
'Carbon':{'Elements':{'C':{'Num':1.}},'Density':2.27,},
'Titanium':{'Elements':{'Ti':{'Num':1.}},'Density':4.51,},
'TiO2-rutile':{'Elements':{'Ti':{'Num':2.},'O':{'Num':4.}},'Volume':62.452},
'Chromium':{'Elements':{'Cr':{'Num':1.}},'Density':7.19,},
'Nickel':{'Elements':{'Ni':{'Num':4.}},'Density':8.90,},
'Copper':{'Elements':{'Cu':{'Num':4.}},'Density':8.96,},
'Hydroxyapatite':{'Elements':{'Ca':{'Num':5.},'P':{'Num':3.},'O':{'Num':13.},'H':{'Num':1.}},'Density':3.986,},
'Cr2O3':{'Elements':{'Cr':{'Num':2.},'O':{'Num':3.}},'Density':5.206,},
'ZrO2':{'Elements':{'Zr':{'Num':1.},'O':{'Num':3,}},'Density':6.134,},
'Y(0.16)Zr(0.84)O2':{'Elements':{'Y':{'Num':0.16},'Zr':{'Num':0.84},'O':{'Num':2.}},'Density':6.01,},
}
# they should not be duplicated in the UserSubstances.py file:
try:
    import UserSubstances as userFile
    Substances.update(userFile.Substances)
except:
    pass
