
## -*- coding:Latin-1 -*-

"""
    % limes -I -m -n 'file...
    % limes -O -n -c [-s 'sep] 'fmt ['titre] 'file...
    % limes -C 'file
    % limes

Dans la première forme (-I), charge l'ensemble des fichier 'fich et affiche
les indices calculés sur lensemble des méthodes.

Dans la deuxième forme (-O), charge l'ensemble des fichiers 'fich et produit
le fichier fusionné au format 'fmt. 'fmt a l'une des valeurs suivantes :
    spart   Format Spart. Dans ce cas, le premier argument est le titre qui
            sera stocké dans le bloc Project_name.
    csv     Format CSV.

Dans la troisième forme (-C), contrôle simplement le fichier 'file, et
affiche un message d'erreur si le fichier est invalide.

Sans argument (quatrième forme), lance l'interface graphique.

Par défaut, si aucune des options -IOC n'est fournie et que des arguments sont
présents, l'option -C est prise en compte.

Dans tous les cas, le type du fichier est identifié par l'extension :
    .spart      Format Spart
    .xls, .xlsx Format Excel
    .csv        Format CSV
    <autre>     Limes tente d'identifier l'un des format mono-partition ABGD,
                GMYC ou PTP.

Dans le cas des fichiers CSV et Excel, l'extension peut être suivie d'un
complément après un ':' :
    - Pour un fichier CSV, il s'agit du séparateur. Exemple : "fichier.csv:;"
        Le séparateur par défaut est la virgule ','.
    - Pour un fichier Excel, il s'agit du nom ou du numéro (à compter de 1) de
        la feuille. Exemple : "fichier.xls:feuille2" ou "fichier.xls:2". Par
        défaut, la feuille numéro 1 est prise en compte.

Options :
    I   Calcule les indices (voir texte).
    O   Fusionne les fichiers et produit un fichier au format 'fmt (voir texte).
    C   Procède simplement au contrôle syntaxique du fichier 'file (voir texte).
    m   Calcule et affiche les match ratio plutôt que les cTax.
    n   Normalise les noms des échantillons avant fusion.
    c   Ne prend en compte que les échantillons communs à toutes les méthodes
        (éventuellement après normalisation si l'option -n est fournie). Option
        forcée implicitement avec -I.
    s   Précise le séparateur 'sep. Seulement si 'fmt vaut "csv". Virgule par
        défaut.
"""

import sys,getopt,os.path
# Noter que les messages du programme sont bilingues, mais que celui-ci
# n'offre aucun moyen de changer la langue par défaut !

from . import limes
from .kagedlib import print_error
from .limes import get_text

def usage(arg=None):
    if isinstance(arg,Exception):
        print_error(arg)
    print("Usage: limes -I -m -n 'file...\n"
          "       limes -O -n -c [-s 'sep] 'fmt ['titre] 'file...\n"
          "       limes -C 'file\n"
          "       limes",
          file=sys.stderr)
    sys.exit(1)

limes.set_langue(1)

"""
Rend le triplet (a,b,c) où 'a est le path complet du fichier, 'b son type
("spart", "csv", "excel" ou ""), et 'c la données extra suivant le ':' (None
si pas de donnée extra ou si type autre que "csv" ou "excel").
Génère une exception si une données extra est donnée pour un fichier autre
que csv ou excel.
"""
def arg2type(file):
    dir,fich=os.path.split(file)
    nom,ext=os.path.splitext(fich)
    a,dp,b=ext.partition(':')
    if dp:
        ext=a
        extra=b
        fich=nom+ext
    else:
        extra=None
    ext2=ext.lower()
    if ext2==".csv": type="csv"
    elif ext2 in (".xls",".xlsx"): type="excel"
    else:
        if dp:
            raise SyntaxError(
                    get_text("':...' valide seulement pour fichiers "
                             "CSV ou Excel",
                             "':...' expected only for CSV or Excel files"))
        if ext2==".spart": type="spart"
        else: type=""
    return (os.path.join(dir,fich),type,extra)

"""
Lit le fichier 'fich et rend la Source correspondant. Celle-ci est chargée.
Le type est déterminé par l'extension, éventuellement complétée de son extra.
Génère une exception si erreur.
"""
def load(fich):
    fich,type,extra=arg2type(fich)
    if type=="csv":
        from . import calc
        if extra is None: extra=','
        src=calc.Reader_csv(fich,extra)
    elif type=="spart":
        from . import spart
        src=spart.Reader_spart(fich)
    elif type=="excel":
        from . import calc
        if extra is None:
            extra=0
        else:
            try: extra=int(extra)-1
            except: pass
        src=calc.Reader_excel(fich,extra)
    else:
        from . import monofmt
        src=monofmt.Reader_monofmt(fich)
    src.load()
    return src

"""
'args est une liste d'arguments donnant les fichiers à charger. Charge tous
les fichiers par load(), et crée et rend l'Espace intégrant toutes leurs
méthodes. Les noms des échantillons sont normalisés si 'norm vaut True. Les
échantillons sont réduits aux communs si 'common vaut True.
Génère une exception si erreur.
"""
def make_espace(args,norm,common):
    meths=[]
    for f in args:
        meths.extend(load(f).methodes)
    return limes.Espace(meths,common=common,strict=not norm)

def run_indices(args,algo,norm):
    espace=make_espace(args,norm,True)
    pr=limes.Printer(espace)
    print()
    if pr.pralias():
        print()
    fn=pr.prmratio if algo==limes.ALGO_MRATIO else pr.prtable
    fn(True)
    print()
    fn(False)

def run_controle(fich):
    src=load(fich)
    print(get_text("Type %s ; %d partitions ; %d échantillons",
                   "Type %s ; %d partitions ; %d samples")%
                  (src.type,len(src.methodes),len(src.echantillons)))

def run_exporte_spart(args,titre,norm,common):
    from . import spart
    espace=make_espace(args,norm,common)
    spart.Writer_spart(sys.stdout,titre,espace)

def run_exporte_csv(args,norm,common,separ):
    from . import calc
    espace=make_espace(args,norm,common)
    calc.Writer_csv(sys.stdout,espace,separ)

def run_interface():
    try:
        from . import wlimes
    except ImportError:
        usage()

##import pdb
##pdb.set_trace()

algo=limes.ALGO_CTAX
try:
    opt,arg=getopt.getopt(sys.argv[1:],"IOCmncs:")
except getopt.GetoptError as e:
    usage(e)
opt_IOC=None
opt_c=opt_m=opt_n=opt_s=False
separ=","
for o,a in opt:
    if o=="-m":
        algo=limes.ALGO_MRATIO
        opt_m=True
    elif o=="-n": opt_n=True
    elif o=="-c": opt_c=True
    elif o=="-s":
        if len(a)!=1: usage()
        separ=a
        opt_s=True
    else:
        if opt_IOC and opt_IOC!=o: usage()
        opt_IOC=o
if len(arg)==0:
    if opt: usage()
    run_interface()
else:
    if opt_IOC is None: opt_IOC="-C"
    if opt_m and opt_IOC!="-I" or \
       (opt_n or opt_c) and opt_IOC=="-C" or \
       opt_s and opt_IOC!="-O":
        usage()
    try:
        if opt_IOC=="-C":
            if len(arg)>1: usage()
            run_controle(arg[0])
        elif opt_IOC=="-I":
            run_indices(arg,algo,opt_n)
        else: # "-O"
            fmt=arg[0]
            if fmt=="spart":
                if len(arg)<3 or opt_s: usage()
                run_exporte_spart(arg[2:],arg[1],opt_n,opt_c)
            elif fmt=="csv":
                if len(arg)<2: usage()
                run_exporte_csv(arg[1:],opt_n,opt_c,separ)
            else:
                usage()
    except Exception as e:
        print_error(e,titre=True)
        sys.exit(1)
    else:
        sys.exit(0)
