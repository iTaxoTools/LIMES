## -*- coding:Latin-1 -*-

"""
D�finit les classes suivantes :

    Reader_csv()
    Reader_excel()

Ces deux classes h�ritent de Source ; leur m�thode .load() charge le contenu
d'un fichier CSV ou Excel
"""

from itertools import count
from .limes import (Echantillon,Methode,Source,get_text,RedundantNameError,
                    nullcontext)

# -- Lecture des fichiers sources ------------

"""
_calc_Reader(redond)

Reader g�n�rique pour les fichiers de type Excel. Les classes d�riv�es sont
sp�cialis�es dans les fichiers CSV ou XLS/XLSX.

Si 'redond vaut False, _run() g�n�re une exception RedundantNameError si deux
m�thodes ou deux �chantillons portent le m�me nom. Si 'redond vaut True, les
noms redondants sont augment�s d'un suffixe num�rique pour les rendre uniques.

La classe d�riv�e doit d�finir les m�thodes suivantes :

    load()  C'est la m�thode lanc�e par l'utilisateur. Lit l'ensemble du
            fichier, renseigne l'instance et rend la liste des Methode. Cette
            fonction doit ouvrir le contexte et appeler ._run() pour effectuer
            le traitement.

    _getlg() Rend un it�rateur retournant une ligne � chaque appel. La nature
            des lignes retourn�es est quelconque, mais ce sera ces lignes qui
            seront pass�es en argument aux autres fonctions sp�cifiques.

    _cells(lg)
            Rend un it�rateur retournant la valeur de chacune des cellules de
            la ligne 'lg. Les valeurs rendues doivent �tre de type str.

    _cell(lg,ind,fmt)
            Rend la valeur de la cellule � l'indice 'ind de la ligne 'lg. Si
            'fmt vaut True, la valeur rendue doit �tre de type str (t�te de
            ligne). Si 'fmt vaut False, la valeur peut �tre str ou int.

    _nonvide(lg)
            Rend False si le ligne 'lg est vide, True si elle comprend au moins
            une cellule non vide.

    _rewind()
            La lecture du fichier s'effectue en deux passes. Cette m�thode est
            appel�e avant la 2i�me passe pour r�initialiser le reader si
            n�cessaire.

Le sch�ma d'utilisation est le suivant. Pour un classe d�riv�e XX :
    - L'utilisateur cr�e l'instance de la classe XX en fonction du type de
        fichier, avec les arguments sp�cifiques.
    - Il appelle instance.load().
    - La m�thode .load() initialise le contexte (ouvre la source) et appelle
        self._run().
    - Celle-ci est le moteur de lecture impl�ment� dans _calc_Reader. Il
        appelle les diverses fonctions de bases ._getlg(), ._cells(), ._cell(),
        ._nonvide(), ._rewind(), d�velopp�es sp�cifiquement par XX, et affecte
        les attributs .methodes et .echantillons.
    - .load() affecte les diff�rents attributs de l'instance, sp�cifique au
        type, rend la liste des Methode.

La seule m�thode publique des classes d�riv�es de _calc_Reader est donc
.load(), qui rend une liste : chaque �l�ment est une instance de Methode,
correspondant � une colonne du tableau, ordonn�es de gauche � droite.
"""
class _calc_Reader:

    marqueur="LIMES"

    def __init__(self,redond):
        self.__redond=redond

    """
    'vus est l'ensemble des noms d�j� utilis�s. Si 'nom existe dans 'vus,
    g�n�re un nouveau nom en lui accolant un suffixe num�rique. Dans tous les
    cas, rend le nom utile ('nom ou 'nom_N) apr�s l'avoir ajout� dans 'vus.
    """
    def __noredond(self,nom,vus):
        if nom in vus:
            if not self.__redond:
                raise RedundantNameError(
                    get_text("Nom de m�thode ou d'�chantillon <%s> redondant",
                             "Redundant name of method or sample <%s>")%
                    nom)
            for i in count(start=2):
                tt="%s_%d"%(nom,i)
                if tt not in vus:
                    nom=tt
                    break
        vus.add(nom)
        return nom

    """
    Si le marqueur existe dans la ligne 'lg, rend son indice. Sinon, rend
    None.
    """
    def __in_marqueur(self,lg):
        for i,v in enumerate(self._cells(lg)):
            if v==self.marqueur:
                return i
        return None

    """
    'lg est la ligne d'en-t�te. Extrait les titres de colonnes et leur
    indice (il peut y avoir des colonnes vides). Les titres de colonnes sont
    extraits � partir de l'indice 'first. Rend un couple (a,b), o� 'a est la
    liste des titres et 'b la liste, de m�me longueur, de l'indice correspon-
    dant.
    """
    def __mkcols(self,lg,first):
        tt=[]
        ind=[]
        for i,t in enumerate(self._cells(lg)):
            if i>=first and t:
                tt.append(t)
                ind.append(i)
        return (tt,ind)

    """
    'lg est la premi�re ligne de donn�es. Rend l'indice du mot le plus � droite
    avant l'indice 'end. Rend None si la ligne est vide avant 'end.
    """
    def __mkcol0(self,lg,end):
        ind=None
        for i,t in enumerate(self._cells(lg)):
            if i==end:
                break
            if t:
                ind=i
        return ind

    """
    Lit l'ensemble du fichier et affecte .methodes et .echantillons. G�n�re une
    exception si probl�me.
    """
    def _run(self):
        ett=lg1=None
        idx_marqueur=None
        for numlg,lg in enumerate(self._getlg()):
            idx_marqueur=self.__in_marqueur(lg)
            if idx_marqueur is not None:
                ett=lg1=lg
                numett=numlg
                break
            else:
                if self._nonvide(lg):
                    if ett is None:
                        ett=lg
                        numett=numlg
                    elif lg1 is None:
                        lg1=lg
        # A partir d'ici :
        # idx_marqueur  Nu�mro de colonne du marqueur "LIMES", ou None si pas
        #               de marqueur.
        # ett           Ligne donnant les noms des m�thodes.
        # numett        Num�ro de cette ligne.
        # lg1           Premi�re ligne de donn�es si 'idx_marqueur vaut None,
        #               �gale � 'ett sinon.
        
        if ett is None or lg1 is None:
            raise Exception(get_text("Fichier vide","Empty file"))
            # Attention, le fichier peut encore �tre vide si le marqueur
            # a �t� fourni, car dans ce cas 'lg1 n'est pas significatif (on n'a
            # pas lu encore de ligne de donn�e).

        if idx_marqueur is None:
            titres,cols=self.__mkcols(ett,1)
            ok=len(titres)>0
            if ok:
                col0=self.__mkcol0(lg1,cols[0])
                ok=col0 is not None
        else:
            col0=idx_marqueur
            titres,cols=self.__mkcols(ett,col0+1)
            ok=len(titres)>0
        if not ok:
            raise Exception(get_text("Fichier mal form�","Badly formated file"))
            
        # A partir d'ici :
        # col0      Num�ro de la colonne donnant les noms des �chantillons.
        # titres    Liste des noms de m�thodes.
        # cols      Liste des num�ros des colonnes de m�thodes.

        codesespeces=[[] for _ in titres]
        # Attention, ne pas remplacer par [[]]*len(titres) !
        self.echantillons=[]
        self._rewind()
        s=set()
        vu=False
        for numlg,lg in enumerate(self._getlg()):
            if numlg>numett:
                ech=self._cell(lg,col0,True)
                if ech:
                    self.echantillons.append(Echantillon(self.__noredond(ech,s)))
                    for e,esp in zip(cols,codesespeces):
                        v=self._cell(lg,e,False)
                        if not v:
                            raise Exception(get_text("Cellule vide (%dx%d)",
                                                     "Empty cell (%dx%d)")%
                                            (numlg+1,e+1))
                        if v in ("-","?"): v=None
                        esp.append(v)
                    vu=True
        if not vu:
            raise Exception(get_text("Fichier vide","Empty file"))
            # Ceci garantit que le nombre d'�chantillons des m�thodes produites
            # est >=1.
        s=set()
        self.methodes=[]
        for titre,esp in zip(titres,codesespeces):
            ll=[(ech,cd) for ech,cd in zip(self.echantillons,esp)
                if cd is not None]
            lech,lcd=zip(*ll)
            self.methodes.append(Methode(self.__noredond(titre,s),lech,lcd,
                                         self))

"""
Reader_csv(fich,separ=',',redond=False)

Reader pour le fichier 'fich de format CSV. 'separ est le caract�re s�parateur.

La lecture s'effectue par .load(). Chaque colonne correspond � une m�thode.

Deux formats sont accept�s :
1. La case sup�rieure gauche du tableau doit contenir le mot "DATA". La ligne
correspondante donne les noms de m�thodes, la colonne les noms d'�chantillons.
Les lignes au-dessus de la ligne DATA, et les colonnes � gauche, sont ignor�es.
2. Pas de marqueur "DATA". Dans ce cas, la premi�re ligne non vide repr�sente
la ligne de titres. La colonne non vide la plus � droite (avant la premi�re
colonne de titre) de la premi�re ligne de donn�es est identifi�e comme la
colonne donnant les noms des �chantillons. Les colonnes � gauche de celle-ci
sont ignor�es.

Il peut y avoir des colonnes vides entre les colonnes de m�thodes, ou des
lignes vides entre les lignes d'�chantillons. Les lignes pour lesquelles la
colonne du nom de l'�chantillon est vide sont �galement ignor�es.

Si 'redond vaut False, load() g�n�re une exception RedundantNameError si deux
m�thodes ou deux �chantillons portent le m�me nom. Si 'redond vaut True, les
noms redondants sont augment�s d'un suffixe num�rique ("nom_N") pour les rendre
uniques. (note : il pourrait �tre utile de retourner en r�sultat cette
information).

Les codes-esp�ces sont de type str ou int. Les �chantillons non pris en compte
par une m�thode doivent �tre marqu�s '-' ou '?' : ainsi, toutes les m�thodes
n'ont pas forc�ment le m�me nombre d'�chantillons.

L'instance dispose des attributs et m�thodes suivants, en plus de ceux h�rit�s
de Source :
    .type       "csv".
    .separ      Le caract�re s�parateur.
"""
class Reader_csv(_calc_Reader,Source):
    type="csv"

    def __init__(self,fich,separ=',',redond=False):
        _calc_Reader.__init__(self,redond)
        self.fich=fich
        self.separ=separ
        import csv
        self.__csv=csv

    """
    Proc�de � la lecture du fichier, et rend une liste d'instances de Methode
    extraites du fichier CSV, dans l'ordre du fichier source, de gauche �
    droite.
    Pour toutes les m�thodes, les �chantillons sont ordonn�s dans l'ordre du
    fichier source, de haut en bas. De plus, un �chantillon est repr�sent� par
    la m�me instance de Echantillon pour toutes les Methode.
    G�n�re une exception si le fichier n'existe pas, ne contient aucune colonne
    de m�thodes ou aucune ligne d'�chantillons, ou est mal form�.
    """
    def load(self):
        if self.methodes is not None:
            return self.methodes
        f=open(self.fich,newline='')
        try:
            with f:
                self.f=f
                self.reader=self.__csv.reader(f,delimiter=self.separ)
                self._run()
                return self.methodes
        except Exception as e:
            raise type(e)(get_text("Ne peut charger le fichier CSV\n%s",
                                   "Cannot load the CSV file %s\n")%self.fich)

    def _getlg(self):
        yield from self.reader

    def _cells(self,lg):
        yield from lg

    def _cell(self,lg,ind,fmt):
        return lg[ind]

    _nonvide=any

    def _rewind(self):
        self.f.seek(0)
        self.reader=self.__csv.reader(self.f,delimiter=self.separ)
        # N�cessaire ?

"""
Reader_excel(fich,feuille=0,redond=False)

Comme Reader_csv(), mais traite un fichier Excel de format .xls ou .xlsx.
'feuille identifie la feuille dans le classeur, soit par son num�ro (� compter
de 0), soit par son nom ; par d�faut, traite la 1i�re feuille.

L'instance dispose des attributs et m�thodes suivants, en plus de ceux h�rit�s
de Source :
    .type       "excel".
    .feuille    Affect� initialement au param�tre 'feuille, puis r�affect�
                apr�s le chargement au nom r�el de la feuille.
"""
class Reader_excel(_calc_Reader,Source):
    type="excel"

    def __init__(self,fich,feuille=0,redond=False):
        _calc_Reader.__init__(self,redond)
        self.fich=fich
        self.feuille=feuille
        import xlrd
        self.__xlrd=xlrd

    """
    Proc�de � la lecture du fichier, et rend la liste d'instances de Methode
    extraites du fichier Excel.
    Pour toutes les m�thodes, les �chantillons sont ordonn�s dans l'ordre du
    fichier source, de haut en bas. De plus, un �chantillon est repr�sent� par
    la m�me instance de Echantillon pour toutes les Methode.
    G�n�re une exception si le fichier n'existe pas, ne contient aucune colonne
    de m�thodes ou aucune ligne d'�chantillons, ou est mal form�.
    """
    def load(self):
        if self.methodes is not None:
            return self.methodes
        f=self.__xlrd.open_workbook(self.fich,on_demand=True)
        try:
            with f:
                self.sheet=f.sheet_by_index(self.feuille) \
                                    if isinstance(self.feuille,int) \
                                    else f.sheet_by_name(self.feuille)
                try:
                    self._run()
                    self.feuille=self.sheet.name
                    return self.methodes
                finally:
                    f.unload_sheet(self.feuille)
                    # N�cessaire ? On ne sait pas si le contexte de 'f lib�re toutes
                    # les ressources, y compris celles du sheet.
        except Exception as e:
            raise type(e)(get_text("Ne peut charger le fichier Excel\n%s",
                                   "Cannot load the Excel file %s\n")%
                          self.fich)

    def _getlg(self):
        for i in range(self.sheet.nrows):
            yield self.sheet.row(i)

    def _cells(self,lg):
        for c in lg:
            yield str(c.value)

    def _cell(self,lg,ind,fmt):
        c=lg[ind]
        v=c.value
        if not isinstance(v,str):
            if c.ctype==self.__xlrd.XL_CELL_DATE:
                raise Exception(get_text("Cellule de type date",
                                         "Date-type cell"))
            v=int(v)
            if fmt: v=str(v)
        return v

    def _nonvide(self,lg):
        for c in lg:
            if c.ctype!=self.__xlrd.XL_CELL_EMPTY:
                return True
        return False

    def _rewind(self):
        pass

"""
Sauvegarde l'Espace espace dans le fichier 'fich. 'separ est le s�parateur de
champs. 'fich peut �tre un objet file-like d�j� ouvert.
"""
def Writer_csv(fich,espace,separ=','):
    if isinstance(fich,str):
        cm=open(fich,"w")
    else:
        cm=nullcontext(fich)
    with cm as f:
        f.write(Reader_csv.marqueur)
        for m in espace:
            f.write("%s%s"%(separ,m.nom))
        f.write("\n")
        for e in espace.echantillons:
            f.write(e.nom)
            for m in espace:
                f.write("%s%s"%(separ,str(m.get(e,"-"))))
            f.write("\n")

##def Writer_csv(espace,fich,separ=','):
##    with open(fich,"w") as f:
##        f.write(Reader.marqueur)
##        for m in espace:
##            f.write("%s%s"%(separ,m.nom))
##        f.write("\n")
##        dm=[dict(m.items()) for m in espace]
##        for e in espace.echantillons():
##            f.write(e.nom)
##            for d in dm:
##                f.write("%s%s"%(separ,str(d[e])))
##            f.write("\n")
